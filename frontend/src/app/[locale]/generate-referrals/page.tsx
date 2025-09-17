'use client';
import { Button } from "@/src/components/ui/button"
import { Label } from "@/src/components/ui/label"
import { Textarea } from "@/src/components/ui/textarea"
import {Resource} from "@/src/types/resources";

import {useState} from 'react';


export default function Page() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<Resource[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const base = process.env.NEXT_PUBLIC_BASE_PATH ?? '';
      const res = await fetch(`${base}/api/generate-referrals`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ text }),
      });

      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();
      setResult(data.result ?? JSON.stringify(data));
    } catch (e: any) {
      setError(e.message ?? 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  return <>
    <div className="">
      <form className="">
        {/* grid w-full max-w-sm items-center gap-3 */}
        <Label htmlFor="client-details">Client Details</Label>
        <Textarea
          id="client-details"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Add client details here…"
          rows={4}
        />
        <Button type="button" onClick={handleClick} disabled={loading} className="margin-top-2">
          {loading ? 'Generating...' : 'Generate Referrals'}
        </Button>
      </form>

      {displayResourcesFromResult(result)}
    </div>
  </>;
}

function displayResourcesFromResult(result: Resource[] | null){
  if (result == null) return null;
  if (result.length === 0) return <div className="margin-top-2">No resources found.</div>;

  return (
    <ul className="usa-list margin-top-3">
      {result.map((r, i) => (
        <li key={i} className="margin-bottom-2">
          <strong className="display-block">{r.name}</strong>

          {r.description && (
            <div className="text-base">{r.description}</div>
          )}

          {r.justification && (
            <div className="font-mono text-sm margin-top-1">
              <span className="text-semibold">Why:</span> {r.justification}
            </div>
          )}

          {r.addresses?.length > 0 && (
            <div className="margin-top-1">
              <span className="text-semibold">Address{r.addresses.length > 1 ? 'es' : ''}:</span>
              <ul className="usa-list usa-list--unstyled margin-top-05">
                {r.addresses.map((a, j) => <li key={j}>{a}</li>)}
              </ul>
            </div>
          )}

          {r.phones?.length > 0 && (
            <div className="margin-top-05">
              <span className="text-semibold">Phone{r.phones.length > 1 ? 's' : ''}:</span>{' '}
              {r.phones.join(', ')}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}