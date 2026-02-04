/**
 * Timeout configurations for various API calls and UI operations (in milliseconds)
 */

/** Timeout for undo notification display - 7.5 seconds */
export const UNDO_NOTIFICATION_TIMEOUT = 7500;

/** Timeout for email sending requests - 5 minutes */
export const EMAIL_TIMEOUT = 300_000;

/** Timeout for action plan generation - 2 minutes */
export const ACTION_PLAN_TIMEOUT = 120_000;

/** Timeout for streaming requests - 10 minutes */
export const STREAMING_TIMEOUT = 600_000;

/** Timeout for FCC location lookup requests - 5 seconds */
export const LOCATION_FETCH_TIMEOUT = 5000;

/** Timeout for "No resources found" message - 12 seconds */
export const NO_RESOURCES_TIMEOUT = 12_000;
