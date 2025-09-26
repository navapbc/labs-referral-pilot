import { Resource } from "@/types/resources";
import {NextResponse} from "next/server";
import { z } from "zod";

const ResourcesSchema = z.object({
  name: z.string(),
  website: z.string().url().optional().default(""),
  addresses: z.array(z.any()).optional().default([]),
  emails: z.array(z.any()).optional().default([]),
  phones: z.array(z.any()).optional().default([]),
  description: z.string().optional(),
  justification: z.string().optional(),
});

// TODO update the logic above to be ready for when we deploy to a PROD env
const generateReferralsURL = process.env.ENVIRONMENT = "https://referral-pilot-dev.navateam.com/generate_referrals/run";//"dev" ? "https://referral-pilot-dev.navateam.com/generate_referrals/run" : "http://0.0.0.0:3000/generate_referrals/run";

export async function fetchResources(clientDescription: string){
  const url = generateReferralsURL;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${process.env.EXTERNAL_API_KEY}`, // no NEXT_PUBLIC here   ---
  };

  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 30_000); // TODO make configurable

  const upstream = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({ query: clientDescription }),
    cache: "no-store",
    signal: ac.signal,
  });

  clearTimeout(timer);

  if (!upstream.ok) {
    const errText = await upstream.text().catch(() => "");
    return NextResponse.json(
      { error: errText || "External API error" },
      { status: upstream.status },
    );
  }

  const responseData = await upstream.text();
  return NextResponse.json(
    { result: parseResources(responseData) },
    { status: 200 },
  );
}

function safeParse<T = any>(s: string): T | null {
  try {
    return JSON.parse(s) as T;
  } catch {
    return null;
  }
}

function parseResources(input: string): Resource[] {
  const root: any =
    typeof input === "string"
      ? (safeParse(input) ?? { result: input })
      : (input ?? {});

  let inner: any | null =
    typeof root?.result === "string" ? safeParse(root.result) : null;

  if (!inner) {
    const replies: any[] =
      root?.result?.llm?.replies ?? root?.llm?.replies ?? [];
    for (const r of replies) {
      const contents: any[] = r?._content ?? [];
      for (const c of contents) {
        if (typeof c?.text === "string") {
          inner = safeParse(c.text);
          if (inner) break;
        }
      }
      if (inner) break;
    }
  }

  if (!inner && Array.isArray(root?.result?.resources)) inner = root.result;
  if (!inner && Array.isArray(root?.resources)) inner = root;

  const resources: any[] = inner?.resources ?? [];
  if (!Array.isArray(resources)) return [];

  // ------------- Here's the Zod parsing that is not working -------------------
/*
  const parsed = ResourcesSchema.safeParse(resources);
  if (!parsed.success) {
    // Optionally log parsed.error.format() for diagnostics
    return [];
  }
  // @ts-ignore
  return parsed.data as Resource[];

*/

  //---------------- Here's what works -----------------------------
  return resources.map((r: Resource) => ({
    name: String(r?.name ?? "error"),
    website: String(r?.website ?? "error"),
    addresses: Array.isArray(r?.addresses) ? r.addresses : [],
    emails: Array.isArray(r?.emails) ? r.emails : [],
    phones: Array.isArray(r?.phones) ? r.phones : [],
    description: typeof r?.description === "string" ? r.description : "",
    justification:
      typeof r?.justification === "string" ? r.justification : undefined,
  })) as Resource[];
}
