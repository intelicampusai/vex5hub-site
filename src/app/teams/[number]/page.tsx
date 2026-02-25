import TeamDetailClient from "./TeamDetailClient";

// Fetch a fixed set of known top teams to pre-render at build
// Additional teams viewed via client-side navigation will still work
// because the client component fetches dynamically from the API
export async function generateStaticParams() {
    try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!apiUrl) return [{ number: '3150N' }];

        const res = await fetch(`${apiUrl}/teams?season=197`, {
            headers: { 'Accept': 'application/json' }
        });
        if (!res.ok) return [{ number: '3150N' }];

        const teams = await res.json();
        if (Array.isArray(teams) && teams.length > 0) {
            return teams.slice(0, 150).map((t: { number: string }) => ({ number: t.number }));
        }
    } catch {
        // fallback
    }
    return [{ number: '3150N' }];
}

export const dynamicParams = false;

export default function TeamDetailPage() {
    return <TeamDetailClient />;
}
