import { z } from "zod";

export const ResourceSchema = z.object({
  addresses: z.array(z.string().optional()).optional(),
  description: z.string().optional(),
  emails: z.array(z.string().email().optional()).optional(),
  justification: z.string().optional(),
  name: z.string(),
  phones: z.array(z.string().optional()).optional(),
  website: z.string().optional().or(z.literal("")),
  referral_type: z.enum(["external", "goodwill", "government"]).optional(),
});

export const ResourcesSchema = z.object({
  resources: z.array(ResourceSchema),
});

export type Resource = z.infer<typeof ResourceSchema>;
export type Resources = z.infer<typeof ResourcesSchema>;
