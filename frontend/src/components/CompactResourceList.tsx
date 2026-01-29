import { Resource } from "@/types/resources";
import { MapPin, Phone, Globe, Mail } from "lucide-react";

interface CompactResourceListProps {
  resources: Resource[];
}

/**
 * A compact list of resources showing only contact information (no descriptions).
 * Used in the "Action Plan Only" print mode to provide reference info for selected resources.
 */
export function CompactResourceList({ resources }: CompactResourceListProps) {
  if (resources.length === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="text-base font-semibold text-gray-900 mb-3">
        Selected Resources - Contact Information
      </h3>
      <div className="space-y-3">
        {resources.map((resource, index) => (
          <div
            key={resource.name}
            className="border border-gray-200 rounded-lg p-3 bg-white"
          >
            <div className="flex items-start gap-2">
              <span className="text-sm font-medium text-gray-500 min-w-[20px]">
                {index + 1}.
              </span>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-gray-900 text-sm">
                  {resource.name}
                </h4>
                <div className="mt-1 space-y-1 text-sm text-gray-600">
                  {resource.addresses && resource.addresses.length > 0 && (
                    <div className="flex items-start gap-2">
                      <MapPin
                        className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400"
                        aria-hidden="true"
                      />
                      <span>
                        {resource.addresses.filter(Boolean).join(" | ")}
                      </span>
                    </div>
                  )}
                  {resource.phones && resource.phones.length > 0 && (
                    <div className="flex items-start gap-2">
                      <Phone
                        className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400"
                        aria-hidden="true"
                      />
                      <span>{resource.phones.filter(Boolean).join(" | ")}</span>
                    </div>
                  )}
                  {resource.website && (
                    <div className="flex items-start gap-2">
                      <Globe
                        className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400"
                        aria-hidden="true"
                      />
                      <a
                        href={resource.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline break-all"
                      >
                        {resource.website}
                      </a>
                    </div>
                  )}
                  {resource.emails && resource.emails.length > 0 && (
                    <div className="flex items-start gap-2">
                      <Mail
                        className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400"
                        aria-hidden="true"
                      />
                      <span>{resource.emails.filter(Boolean).join(" | ")}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
