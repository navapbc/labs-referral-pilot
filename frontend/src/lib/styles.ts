/** Resource type color mapping for borders, badges, and text */
export const RESOURCE_TYPE_COLORS = {
  goodwill: {
    border: "border-t-blue-600",
    badge: "bg-blue-600",
    text: "text-blue-800",
  },
  government: {
    border: "border-t-gray-600",
    badge: "bg-gray-600",
    text: "text-gray-800",
  },
  external: {
    border: "border-t-green-600",
    badge: "bg-green-600",
    text: "text-green-800",
  },
} as const;

export type ReferralType = keyof typeof RESOURCE_TYPE_COLORS;

const LOADING_COLORS = {
  border: "border-t-gray-300",
  badge: "bg-gray-300",
  text: "text-gray-400",
} as const;

export function getResourceTypeColors(referralType: string | undefined) {
  if (referralType && referralType in RESOURCE_TYPE_COLORS) {
    return RESOURCE_TYPE_COLORS[referralType as ReferralType];
  }
  return LOADING_COLORS;
}
