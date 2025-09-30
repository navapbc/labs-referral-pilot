import { z } from "zod";

export const ResourceSchema = z.object({
  name: z.string(),
  addresses: z.array(z.string()).optional(),
  phones: z.array(z.string()).optional(),
  emails: z.array(z.string().email()).optional(),
  website: z.string().url().optional().or(z.literal("")),
  description: z.string().optional(),
  justification: z.string().optional(),
});

export const ResourcesSchema = z.object({
  resources: z.array(ResourceSchema),
});

export type Resource = z.infer<typeof ResourceSchema>;
export type Resources = z.infer<typeof ResourcesSchema>;
