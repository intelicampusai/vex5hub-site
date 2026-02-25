'use client';

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { getTeams, getTopRegions } from "@/lib/api";
import { TeamCard } from "@/components/dashboard/TeamCard";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Trophy } from "lucide-react";

function TeamsContent() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const query = searchParams.get('q') || "";

    const selectedGrade = searchParams.get('grade') || "All";
    const selectedRegion = searchParams.get('region') || "All";

    const [teams, setTeams] = useState<any[]>([]);
    const [regions, setRegions] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);

    const [showQualified, setShowQualified] = useState(false);

    useEffect(() => {
        getTopRegions().then(setRegions).catch(console.error);
    }, []);

    useEffect(() => {
        getTopRegions().then(setRegions).catch(console.error);
    }, []);

    useEffect(() => {
        const fetchTeams = async () => {

            setLoading(true);
            try {
                const allTeams = await getTeams(query);
                const filtered = allTeams.filter(t => {
                    const gradeMatch = selectedGrade === "All" || t.grade === selectedGrade;

                    let regionMatch = true;
                    if (selectedRegion !== "All") {
                        if (["United States", "China", "Canada"].includes(selectedRegion)) {
                            regionMatch = t.country === selectedRegion;
                        } else {
                            regionMatch = t.region === selectedRegion; // e.g. "Ontario", "British Columbia", "California"
                        }
                    }

                    const qualifiedMatch = !showQualified || t.worlds_qualified === true;

                    return gradeMatch && regionMatch && qualifiedMatch;
                });
                setTeams(filtered);
            } catch (error) {
                console.error("Failed to fetch teams:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchTeams();

    }, [query, selectedGrade, selectedRegion, showQualified]);

    const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const q = formData.get('q') as string;
        const params = new URLSearchParams(searchParams.toString());
        if (q) params.set('q', q);
        else params.delete('q');
        router.push(`/teams?${params.toString()}`);
    };

    const handleGradeFilter = (grade: string) => {
        const params = new URLSearchParams(searchParams.toString());
        if (grade === 'All') params.delete('grade');
        else params.set('grade', grade);
        router.push(`/teams?${params.toString()}`);
    };

    const handleRegionFilter = (region: string) => {
        const params = new URLSearchParams(searchParams.toString());
        if (region === 'All') params.delete('region');
        else params.set('region', region);
        router.push(`/teams?${params.toString()}`);
    };

    return (
        <div className="space-y-4">
            <div className="sticky top-14 z-40 bg-background/95 backdrop-blur py-2 -mx-4 px-4 border-b md:static md:bg-transparent md:border-none md:p-0 md:m-0 flex flex-col sm:flex-row gap-2">
                <form onSubmit={handleSearch} className="flex space-x-2 flex-1">
                    <div className="relative flex-1">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            name="q"
                            placeholder="Search teams (e.g. 3150N)..."
                            className="pl-8"
                            defaultValue={query}
                        />
                    </div>
                    <Button type="submit">Search</Button>
                </form>

                <div className="flex gap-2 items-center">
                    <select
                        className="h-10 w-[180px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        value={selectedRegion}
                        onChange={(e) => handleRegionFilter(e.target.value)}
                    >
                        <option value="All">All Regions</option>
                        {regions.length > 0 && (
                            <optgroup label="Top Performing Regions">
                                {regions.map(r => (
                                    <option key={r} value={r}>{r}</option>
                                ))}
                            </optgroup>
                        )}
                        <optgroup label="Other">
                            <option value="United States">United States</option>
                            <option value="China">China</option>
                            <option value="Canada">Canada</option>
                        </optgroup>
                    </select>

                    <div className="flex bg-muted rounded-md p-1 gap-1">
                        <Button
                            variant={selectedGrade === "All" ? "default" : "outline"}
                            onClick={() => handleGradeFilter('All')}
                            className="h-8"
                        >
                            All
                        </Button>
                        <Button
                            variant={selectedGrade === "High School" ? "default" : "outline"}
                            onClick={() => handleGradeFilter('High School')}
                            className="h-8"
                        >
                            HS
                        </Button>
                        <Button
                            variant={selectedGrade === "Middle School" ? "default" : "outline"}
                            onClick={() => handleGradeFilter('Middle School')}
                            className="h-8"
                        >
                            MS
                        </Button>
                    </div>

                    <Button
                        variant={showQualified ? "default" : "outline"}
                        onClick={() => setShowQualified(!showQualified)}
                        className="gap-2"
                        title="Show World Championship Qualified Teams Only"
                    >
                        <Trophy className="h-4 w-4" />
                        <span className="hidden sm:inline">Worlds Qualified</span>
                    </Button>
                </div>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 opacity-50">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="h-48 bg-muted animate-pulse rounded-lg" />
                    ))}
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {teams.length > 0 ? (
                        teams.map((team) => (
                            <TeamCard key={team.id} team={team} />
                        ))
                    ) : (
                        <div className="col-span-full text-center py-10 text-muted-foreground">
                            No teams found matching "{query}"
                            {selectedGrade !== "All" ? ` in ${selectedGrade}` : ""}
                            {selectedRegion !== "All" ? ` in ${selectedRegion}` : ""}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default function TeamsPage() {
    return (
        <Suspense fallback={<div>Loading teams...</div>}>
            <TeamsContent />
        </Suspense>
    );
}
