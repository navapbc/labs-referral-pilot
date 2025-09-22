// src/app/api/generate-referrals/route.ts
import { NextRequest, NextResponse } from 'next/server';
import {Resource} from "@/src/types/resources";

const generateReferralsURL = "https://referral-pilot-dev.navateam.com/generate_referrals/run" // process.env.ENVIRONMENT == "dev" ? "https://referral-pilot-dev.navateam.com/generate_referrals/run" : "http://localhost:3000/generate_referrals/run"
console.log(generateReferralsURL) // TODO update the logic above to be ready for when we deploy to a PROD env

export const runtime = 'nodejs'; // (optional) stick to Node for widest compat

export async function POST(req: NextRequest) {
  try {
    const { clientDescription } = await req.json();
    if (typeof clientDescription !== 'string' || !clientDescription.trim()) {
      return NextResponse.json({ error: 'Invalid `client description`' }, { status: 400 });
    }

    // Build URL + headers (keep secrets on server)
    const url = generateReferralsURL;
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.EXTERNAL_API_KEY}`, // no NEXT_PUBLIC here   ---
    };

    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), 30000); // TODO make configurable


    const upstream = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({ query:clientDescription }),
      cache: 'no-store',        // avoid caching responses
      signal: ac.signal,
    });

    clearTimeout(timer);

    if (!upstream.ok) {
      const errText = await upstream.text().catch(() => '');
      return NextResponse.json(
        { error: errText || 'External API error' },
        { status: upstream.status }
      );
    }

    const responseData = await upstream.text();
    return NextResponse.json({ result: parseResources(responseData) }, { status: 200 });
  } catch (err: any) {
    if (err?.name === 'AbortError') {
      return NextResponse.json({ error: 'Upstream timeout' }, { status: 504 });
    }
    return NextResponse.json({ error: err?.message ?? 'Server error' }, { status: 500 });
  }
}

function safeParse<T = any>(s: string): T | null {
  try { return JSON.parse(s) as T; } catch { return null; }
}

function parseResources(input: unknown): Resource[] {
  // 1) Normalize input to an object
  const root: any =
    typeof input === 'string' ? (safeParse(input) ?? { result: input }) : input ?? {};

  // 2) Try common locations for the inner JSON string
  //    A) result is a raw string
  let inner: any | null = typeof root?.result === 'string' ? safeParse(root.result) : null;

  //    B) Anthropic-style: result.llm.replies[...]._content[...].text -> JSON string
  if (!inner) {
    const replies: any[] = root?.result?.llm?.replies ?? root?.llm?.replies ?? [];
    for (const r of replies) {
      const contents: any[] = r?._content ?? [];
      for (const c of contents) {
        if (typeof c?.text === 'string') {
          inner = safeParse(c.text);
          if (inner) break;
        }
      }
      if (inner) break;
    }
  }

  //    C) Already an object with resources
  if (!inner && Array.isArray(root?.result?.resources)) inner = root.result;
  if (!inner && Array.isArray(root?.resources)) inner = root;

  const resources: any[] = inner?.resources ?? [];
  if (!Array.isArray(resources)) return [];

  // 3) Normalize fields for easy rendering
  return resources.map((r) => ({
    name: String(r?.resource_name ?? ''),
    addresses: Array.isArray(r?.resource_addresses) ? r.resource_addresses : [],
    phones: Array.isArray(r?.resource_phones) ? r.resource_phones : [],
    description: typeof r?.description === 'string' ? r.description : '',
    justification: typeof r?.justification === 'string' ? r.justification : undefined,
  })) as Resource[];
}
