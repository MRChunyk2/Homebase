/**
 * Billing kill switch.
 *
 * Cloud Billing budgets only SEND ALERTS — they do not stop spending. This
 * function is what turns the $50 budget into an actual hard stop: the budget
 * publishes to the `billing-killswitch` Pub/Sub topic, this function reads the
 * message, and if spend has passed the budget it detaches the billing account
 * from the project.
 *
 * What that does, concretely:
 *   - Hosting keeps serving, Google sign-in keeps working.
 *   - Firestore keeps working within the free (Spark) daily quotas, so the
 *     roster and dashboards keep loading.
 *   - Cloud Storage stops: file uploads fail and stored files stop loading.
 *
 * In other words the site degrades, it does not go down. Re-enable by
 * relinking the billing account in the Firebase console (~30 seconds).
 * Do not leave billing disabled long-term — stored files can be at risk.
 *
 * GOTCHA — it re-trips within the same month. The budget is MONTHLY, so once
 * this has fired the month's spend is already over the limit. Re-linking
 * billing means the next budget notification (several arrive per day) sees you
 * still over budget and disables billing again. After re-linking, either raise
 * the kill-switch budget above the month's actual spend until the 1st, or
 * leave Storage off until the budget resets. The same warning is in the
 * "Homebase — BILLING KILL SWITCH FIRED" Cloud Monitoring alert, which emails
 * will@ and michael@ with full recovery steps when this fires.
 */
const { onMessagePublished } = require('firebase-functions/v2/pubsub');
const logger = require('firebase-functions/logger');

const PROJECT_ID = 'advance-intranet';
const BILLING_INFO = `https://cloudbilling.googleapis.com/v1/projects/${PROJECT_ID}/billingInfo`;

// Token for the function's own service account, from the metadata server.
async function accessToken() {
  const r = await fetch(
    'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
    { headers: { 'Metadata-Flavor': 'Google' } }
  );
  if (!r.ok) throw new Error('metadata token failed: ' + r.status);
  return (await r.json()).access_token;
}

exports.billingKillSwitch = onMessagePublished(
  {
    topic: 'billing-killswitch',
    region: 'us-central1',
    retry: false,
    // Dedicated identity holding Billing Account Administrator. Kept off the
    // default compute service account so no other function inherits the power
    // to switch billing off.
    serviceAccount: 'billing-killswitch@advance-intranet.iam.gserviceaccount.com',
  },
  async (event) => {
    const data = event.data?.message?.json || {};
    const cost = Number(data.costAmount);
    const budget = Number(data.budgetAmount);
    const name = data.budgetDisplayName || '(unnamed budget)';

    logger.info('budget notification', {
      budget: name, cost, budgetAmount: budget,
      threshold: data.alertThresholdExceeded, currency: data.currencyCode,
    });

    if (!Number.isFinite(cost) || !Number.isFinite(budget)) {
      logger.warn('missing cost/budget amounts — ignoring', { data });
      return;
    }

    // Only fire when spend has actually passed the budget. Lower-threshold
    // notifications (50%, 90%) fall through here and do nothing.
    if (cost <= budget) {
      logger.info(`under budget ($${cost} of $${budget}) — no action`);
      return;
    }

    const token = await accessToken();
    const headers = { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' };

    // Read current state — but never treat an UNREADABLE response as "already
    // disabled". Only a positive confirmation that billing is off is grounds
    // for skipping; anything else falls through and still attempts the
    // disable, because the entire point is to stop the spend.
    const curRes = await fetch(BILLING_INFO, { headers });
    if (curRes.ok) {
      const cur = await curRes.json().catch(() => ({}));
      if (cur.billingEnabled === false) {
        logger.info('billing already disabled — nothing to do');
        return;
      }
    } else {
      logger.warn(`could not read billing state (HTTP ${curRes.status}) — ` +
        'attempting the disable anyway');
    }

    logger.error(`SPEND EXCEEDED: $${cost} of $${budget} on "${name}" — DISABLING BILLING`);
    const res = await fetch(BILLING_INFO, {
      method: 'PUT', headers, body: JSON.stringify({ billingAccountName: '' }),
    });
    const body = await res.json().catch(() => ({}));

    if (res.ok && body.billingEnabled === false) {
      logger.error('BILLING DISABLED for ' + PROJECT_ID + '. Storage is now offline; ' +
        'Hosting and Firestore (free quotas) keep running. Relink billing in the ' +
        'Firebase console to restore — but note the budget is MONTHLY, so after ' +
        'relinking you must raise the budget above this month\'s spend or this ' +
        'will fire again within hours.');
    } else {
      logger.error('FAILED to disable billing — check that this function\'s service ' +
        'account has the Billing Account Administrator role.',
        { status: res.status, body });
    }
  }
);
