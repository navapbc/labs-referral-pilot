import { z } from "zod";

export const ResourceSchema = z.object({
  name: z.string(),
  addresses: z.array(z.string()),
  phones: z.array(z.string()),
  emails: z.array(z.string().email()),
  website: z.string().url(),
  description: z.string(),
  justification: z.string(),
});

export const ResourcesSchema = z.object({
  resources: z.array(ResourceSchema),
});

export type Resource = z.infer<typeof ResourceSchema>;
export type Resources = z.infer<typeof ResourcesSchema>;
