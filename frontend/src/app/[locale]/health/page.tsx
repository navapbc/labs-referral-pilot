import { getApiDomain } from "@/src/util/apiDomain";

export default async function Page() {
  return <>healthy, env: {await getApiDomain()}</>;
}
