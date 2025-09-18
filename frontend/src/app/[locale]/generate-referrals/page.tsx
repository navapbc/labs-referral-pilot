'use client';
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {Resource} from "@/src/types/resources";

import {useState} from 'react';
import {Sparkles} from "lucide-react";


export default function Page() {
  const [clientDescription, setClientDescription] = useState("")
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
        body: JSON.stringify({ clientDescription }),
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
      <div>
        <div className="space-y-3">
          <Textarea
            placeholder="Add additional details about the client's specific situation, needs, and circumstances here..."
            name="clientDescriptionInput"
            value={clientDescription}
            onChange={(e) => setClientDescription(e.target.value)}
            className="min-h-[350px] text-base border-gray-300 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <Button
          type="button"
          onClick={() => handleClick()}
          disabled={!clientDescription.trim() || loading}
          style={{
            backgroundColor: "#2563eb",
            color: "#ffffff",
            padding: "12px 32px",
            fontSize: "18px",
            fontWeight: "500",
            borderRadius: "6px",
            border: "none",
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
            transition: "all 0.2s ease-in-out",
          }}
        >
          <Sparkles className="w-5 h-5" />
          {loading ? "Generating Resources..." : "Find Resources"}
        </Button>
      </div>
      {displayResourcesFromResult(result)}
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