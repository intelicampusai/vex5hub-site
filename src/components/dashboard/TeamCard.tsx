
import { Team } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Trophy, Zap, Gamepad2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface TeamCardProps {
    team: Team;
    compact?: boolean;
}

export function TeamCard({ team, compact = false }: TeamCardProps) {
    const winRate = team.stats ? ((team.stats.wins / team.stats.total_matches) * 100).toFixed(0) : "0";

    return (
        <Link href={`/teams/${team.number}`}>
            <Card className="h-full hover:bg-accent/50 transition-colors cursor-pointer group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-xl font-bold font-mono group-hover:underline decoration-primary">
                        {team.number}
                    </CardTitle>
                    <div className="flex gap-2">
                        {team.grade && (
                            <Badge
                                variant={team.grade === 'High School' ? 'default' : 'outline'}
                                className={cn("text-xs px-2 py-0 h-5",
                                    team.grade === 'Middle School' && "bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800"
                                )}
                            >
                                {team.grade === 'High School' ? 'HS' : 'MS'}
                            </Badge>
                        )}
                        {team.stats && (
                            <Badge variant={team.stats.rank <= 10 ? "secondary" : "outline"} className="text-xs px-2 py-0 h-5">
                                Rank #{team.stats.rank}
                            </Badge>
                        )}
                        {team.skills && (
                            <Badge variant="outline" className="text-xs px-2 py-0 h-5 border-blue-200 text-blue-700 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800">
                                Skills #{team.skills.rank}
                            </Badge>
                        )}
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="text-sm text-muted-foreground mb-1 truncate">
                        {team.name} <span className="text-xs opacity-50">• {team.organization}</span>
                    </div>
                    <div className="text-xs text-muted-foreground mb-4 truncate opacity-80">
                        {team.region}, {team.country}
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="flex flex-col">
                            <span className="text-muted-foreground text-xs uppercase font-semibold">Record</span>
                            <div className="flex items-center space-x-1 font-mono">
                                <span className="text-green-600 font-bold">{team.stats?.wins}W</span>
                                <span className="text-muted-foreground">-</span>
                                <span className="text-red-500 font-bold">{team.stats?.losses}L</span>
                                <span className="text-muted-foreground">-</span>
                                <span className="text-yellow-600 font-bold">{team.stats?.ties}T</span>
                            </div>
                        </div>

                        <div className="flex flex-col">
                            <span className="text-muted-foreground text-xs uppercase font-semibold">Skills</span>
                            <div className="flex items-baseline space-x-1">
                                <span className="font-bold text-lg">{team.skills?.combined_score || 0}</span>
                                <span className="text-xs text-muted-foreground">pts</span>
                            </div>
                        </div>
                    </div>

                    {team.skills && (
                        <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-2 text-xs">
                            <div className="flex items-center space-x-1" title="Driver Skills">
                                <Gamepad2 className="h-3 w-3 text-blue-500" />
                                <span>Driver: {team.skills.driver_score}</span>
                            </div>
                            <div className="flex items-center space-x-1" title="Autonomous Coding Skills">
                                <Zap className="h-3 w-3 text-purple-500" />
                                <span>Auto: {team.skills.programming_score}</span>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </Link>
    );
}
