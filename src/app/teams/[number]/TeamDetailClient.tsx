'use client';

import { useState, useEffect } from 'react';
import { useParams } from "next/navigation";
import { getTeam, getMatches, getTeamEvents } from "@/lib/api";
import { Team, Match, TeamEvent } from "@/types";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Video, ArrowLeft, Trophy, Target, ChevronDown, ChevronUp, Calendar, MapPin, Radio, ExternalLink } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface TeamDetailClientProps {
    teamNumber?: string;
}

export default function TeamDetailClient({ teamNumber }: TeamDetailClientProps) {
    const params = useParams();
    const number = teamNumber || (params?.number as string);

    const [team, setTeam] = useState<Team | null>(null);
    const [matches, setMatches] = useState<Match[]>([]);
    const [teamEvents, setTeamEvents] = useState<TeamEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [matchesLoading, setMatchesLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!number) return;

        const fetchTeam = async () => {
            try {
                setLoading(true);
                const teamData = await getTeam(number);
                if (!teamData) { setError(true); return; }
                setTeam(teamData);
            } catch (err) {
                console.error("Error fetching team:", err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        const fetchMatches = async () => {
            try {
                setMatchesLoading(true);
                const matchData = await getMatches(number);
                setMatches(matchData);
            } catch (err) {
                console.error("Error fetching matches:", err);
            } finally {
                setMatchesLoading(false);
            }
        };

        const fetchTeamEvents = async () => {
            try {
                const eventsData = await getTeamEvents(number);
                setTeamEvents(eventsData);
            } catch (err) {
                console.error("Error fetching team events:", err);
            }
        };

        fetchTeam();
        fetchMatches();
        fetchTeamEvents();
    }, [number]);

    if (loading) {
        return (
            <div className="space-y-6 pb-10 animate-pulse">
                <div className="h-4 w-48 bg-muted rounded"></div>
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div className="space-y-2">
                        <div className="h-10 w-32 bg-muted rounded"></div>
                        <div className="h-6 w-64 bg-muted rounded"></div>
                        <div className="h-4 w-48 bg-muted rounded"></div>
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="h-32 bg-muted rounded"></div>
                    <div className="h-32 bg-muted rounded"></div>
                </div>
            </div>
        );
    }

    if (error || !team) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <h2 className="text-2xl font-bold mb-2">Team Not Found</h2>
                <p className="text-muted-foreground mb-6">Could not find team {number}</p>
                <Button asChild>
                    <Link href="/teams">Return to Teams</Link>
                </Button>
            </div>
        );
    }

    // Derive win/loss/tie counts from match data
    const playedMatches = matches.filter(m => m.my_score !== undefined && m.opp_score !== undefined);
    const wins = playedMatches.filter(m => m.won === true).length;
    const losses = playedMatches.filter(m => m.won === false && m.my_score !== m.opp_score).length;
    const ties = playedMatches.filter(m => m.my_score === m.opp_score).length;
    const winRate = playedMatches.length > 0 ? ((wins / playedMatches.length) * 100).toFixed(1) : "0.0";

    return (
        <div className="space-y-6 pb-10">
            {/* Breadcrumbs */}
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <Link href="/teams" className="hover:text-primary flex items-center">
                    <ArrowLeft className="mr-1 h-3 w-3" /> Teams
                </Link>
                <span>/</span>
                <span className="text-foreground font-medium">{team.number}</span>
            </div>

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-black tracking-tight">{team.number}</h1>
                    <p className="text-xl text-muted-foreground">{team.name}</p>
                    <p className="text-sm opacity-70">{team.organization} • {team.region}, {team.country}</p>
                </div>
                <div className="flex space-x-2">
                    <Badge variant="outline" className="text-sm px-3 py-1">{team.grade}</Badge>
                    {team.skills?.rank && (
                        <Badge className="text-sm px-3 py-1">Skills #{team.skills.rank}</Badge>
                    )}
                    {team.worlds_qualified && (
                        <Badge variant="default" className="text-sm px-3 py-1 bg-yellow-500 hover:bg-yellow-600 text-black">
                            🌍 Worlds Qualified
                        </Badge>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                            <Trophy className="mr-2 h-4 w-4 text-yellow-500" /> Season Record
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold font-mono">
                            {wins} - {losses} - {ties}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            {playedMatches.length} Matches · {winRate}% Win Rate
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                            <Target className="mr-2 h-4 w-4 text-blue-500" /> Skills Score
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{team.skills?.combined_score || 0}</div>
                        <div className="flex gap-3 mt-1">
                            <p className="text-xs text-muted-foreground">
                                Driver: <span className="font-semibold">{team.skills?.driver || 0}</span>
                            </p>
                            <p className="text-xs text-muted-foreground">
                                Programming: <span className="font-semibold">{team.skills?.programming || 0}</span>
                            </p>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Skills Rank: #{team.skills?.rank || "N/A"}
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* Upcoming / Live Events */}
            {teamEvents.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-2xl font-bold tracking-tight px-1 flex items-center gap-2">
                        <Calendar className="h-6 w-6 text-blue-500" />
                        Upcoming Events
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {teamEvents.map((evt) => {
                            const startDate = evt.start ? new Date(evt.start) : null;
                            const endDate = evt.end ? new Date(evt.end) : null;
                            const isLive = evt.status === 'active';

                            const formatDate = (d: Date) =>
                                d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

                            let dateStr = '';
                            if (startDate && endDate) {
                                const sameDay = startDate.toDateString() === endDate.toDateString();
                                dateStr = sameDay
                                    ? formatDate(startDate)
                                    : `${formatDate(startDate)} - ${formatDate(endDate)}`;
                            } else if (startDate) {
                                dateStr = formatDate(startDate);
                            }

                            return (
                                <Card
                                    key={`${evt.sku}-${evt.start}`}
                                    className={cn(
                                        "relative overflow-hidden transition-all",
                                        isLive && "border-green-500/50 shadow-green-500/10 shadow-md"
                                    )}
                                >
                                    {isLive && (
                                        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-green-400 to-emerald-500" />
                                    )}
                                    <CardContent className="pt-5 pb-4">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    {isLive && (
                                                        <Badge className="bg-green-500 text-white text-xs flex items-center gap-1 shrink-0">
                                                            <Radio className="h-3 w-3 animate-pulse" />
                                                            LIVE
                                                        </Badge>
                                                    )}
                                                    {evt.level && (
                                                        <Badge variant="outline" className="text-xs shrink-0">
                                                            {evt.level}
                                                        </Badge>
                                                    )}
                                                </div>
                                                <h3 className="font-semibold text-sm leading-tight line-clamp-2">
                                                    {evt.event_name}
                                                </h3>
                                                <div className="flex flex-col gap-1 mt-2 text-xs text-muted-foreground">
                                                    {dateStr && (
                                                        <span className="flex items-center gap-1">
                                                            <Calendar className="h-3 w-3" />
                                                            {dateStr}
                                                        </span>
                                                    )}
                                                    {evt.location && (
                                                        <span className="flex items-center gap-1">
                                                            <MapPin className="h-3 w-3" />
                                                            {evt.location}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Competition History */}
            <div className="space-y-4">
                <h2 className="text-2xl font-bold tracking-tight px-1">Competition History</h2>

                {matchesLoading ? (
                    <div className="space-y-3 animate-pulse">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-20 bg-muted rounded-lg" />
                        ))}
                    </div>
                ) : matches.length > 0 ? (
                    (() => {
                        // Group matches by event (using event_name + sku for uniqueness)
                        const groups: {
                            [key: string]: {
                                name: string;
                                sku: string;
                                event_start?: string;
                                event_end?: string;
                                event_location?: string;
                                matches: Match[]
                            }
                        } = {};

                        matches.forEach(match => {
                            const key = match.sku || match.event_name;
                            if (!groups[key]) {
                                groups[key] = {
                                    name: match.event_name,
                                    sku: match.sku,
                                    event_start: match.event_start,
                                    event_end: match.event_end,
                                    event_location: match.event_location,
                                    matches: []
                                };
                            }
                            groups[key].matches.push(match);
                        });

                        // Sort groups: most recent first (by event_start, fallback to scheduled date)
                        const sortedGroups = Object.entries(groups).sort(([, a], [, b]) => {
                            const aDate = a.event_start || a.matches[0]?.scheduled || '';
                            const bDate = b.event_start || b.matches[0]?.scheduled || '';
                            return bDate.localeCompare(aDate);
                        });

                        return sortedGroups.map(([key, group]) => (
                            <MatchGroup
                                key={key}
                                eventName={group.name}
                                sku={group.sku}
                                eventStart={group.event_start}
                                eventEnd={group.event_end}
                                eventLocation={group.event_location}
                                matches={group.matches}
                                teamNumber={number}
                            />
                        ));
                    })()
                ) : (
                    <Card>
                        <CardContent className="py-10 text-center text-muted-foreground">
                            No match data found for this team yet.
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}

const ROUND_ORDER: Record<string, number> = {
    'Final': 100,
    'Semifinal': 80,
    'Quarterfinal': 60,
    'Round of 16': 40,
    'Qualification': 20,
    'Practice': 0
};

function MatchGroup({
    eventName, sku, eventStart, eventEnd, eventLocation, matches, teamNumber
}: {
    eventName: string;
    sku: string;
    eventStart?: string;
    eventEnd?: string;
    eventLocation?: string;
    matches: Match[];
    teamNumber: string;
}) {
    const [isOpen, setIsOpen] = useState(true);
    const eventUrl = sku ? `https://www.robotevents.com/${encodeURIComponent(sku)}.html` : null;

    // Sort matches: elims first, then by match_num descending
    const sorted = [...matches].sort((a, b) => {
        const rA = ROUND_ORDER[a.round] ?? 10;
        const rB = ROUND_ORDER[b.round] ?? 10;
        if (rA !== rB) return rB - rA;
        return b.match_num - a.match_num;
    });

    const played = matches.filter(m => m.my_score !== undefined);
    const wins = played.filter(m => m.won).length;
    const losses = played.filter(m => m.won === false && m.my_score !== m.opp_score).length;

    // Build a short match label
    const matchLabel = (match: Match): string => {
        const hasInstance = match.instance && match.instance > 0;
        switch (match.round) {
            case 'Qualification': return `Q${match.match_num}`;
            case 'Practice': return `P${match.match_num}`;
            case 'Final': return hasInstance ? `F ${match.instance}-${match.match_num}` : `F${match.match_num}`;
            case 'Semifinal': return hasInstance ? `SF ${match.instance}-${match.match_num}` : `SF${match.match_num}`;
            case 'Quarterfinal': return hasInstance ? `QF ${match.instance}-${match.match_num}` : `QF${match.match_num}`;
            case 'Round of 16': return hasInstance ? `R16 ${match.instance}-${match.match_num}` : `R16-${match.match_num}`;
            default: return `#${match.match_num}`;
        }
    };

    return (
        <Card className="overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors border-b"
            >
                <div className="flex items-center space-x-3 text-left">
                    <div className="bg-primary/10 p-2 rounded-full">
                        <Calendar className="h-4 w-4 text-primary" />
                    </div>
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <h3 className="font-bold leading-none">{eventName}</h3>
                            {eventUrl && (
                                <Link
                                    href={eventUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    onClick={e => e.stopPropagation()}
                                    className="text-xs text-muted-foreground hover:text-primary inline-flex items-center gap-1"
                                >
                                    RobotEvents
                                    <ExternalLink className="h-3 w-3" />
                                </Link>
                            )}
                        </div>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2">
                            {eventStart && (
                                <div className="flex items-center text-[10px] text-muted-foreground">
                                    <Calendar className="h-3 w-3 mr-1 opacity-70" />
                                    {formatDateRange(eventStart, eventEnd)}
                                </div>
                            )}
                            {eventLocation && (
                                <div className="flex items-center text-[10px] text-muted-foreground">
                                    <MapPin className="h-3 w-3 mr-1 opacity-70" />
                                    {eventLocation}
                                </div>
                            )}
                            <div className="flex items-center text-[10px] text-muted-foreground">
                                <Trophy className="h-3 w-3 mr-1 opacity-70" />
                                {matches.length} Matches
                                {played.length > 0 && (
                                    <span className="ml-1 border-l pl-1">
                                        <span className="text-green-600 dark:text-green-400 font-semibold">{wins}W</span>
                                        {' - '}
                                        <span className="text-red-600 dark:text-red-400 font-semibold">{losses}L</span>
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
                {isOpen
                    ? <ChevronUp className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                    : <ChevronDown className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                }
            </button>

            <div className={cn(!isOpen && "hidden")}>
                <div className="overflow-x-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[80px]">Match</TableHead>
                                <TableHead className="w-[110px]">Result</TableHead>
                                <TableHead>Partners</TableHead>
                                <TableHead>Opponents</TableHead>
                                <TableHead className="text-right w-[60px]">Video</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {sorted.map((match) => {
                                const hasScore = match.my_score !== undefined && match.opp_score !== undefined;
                                const isWin = match.won === true;
                                const isTie = hasScore && match.my_score === match.opp_score;
                                const isRed = match.alliance === 'red';

                                return (
                                    <TableRow key={match.SK}>
                                        {/* Match label */}
                                        <TableCell className="font-medium font-mono text-xs whitespace-nowrap">
                                            {matchLabel(match)}
                                        </TableCell>

                                        {/* Result badge */}
                                        <TableCell>
                                            {hasScore ? (
                                                <Badge
                                                    variant={isWin ? "default" : isTie ? "outline" : "destructive"}
                                                    className="font-mono text-[10px] px-1.5 py-0"
                                                >
                                                    {isWin ? "WIN" : isTie ? "TIE" : "LOSS"}{" "}
                                                    {match.my_score}-{match.opp_score}
                                                </Badge>
                                            ) : (
                                                <span className="text-muted-foreground text-[10px] italic">Unscored</span>
                                            )}
                                        </TableCell>

                                        {/* Partners */}
                                        <TableCell className="text-[11px]">
                                            <div className={cn(
                                                "flex flex-wrap gap-1 px-2 py-0.5 rounded",
                                                isRed
                                                    ? "bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300"
                                                    : "bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300"
                                            )}>
                                                {(match.partner_teams?.length ?? 0) > 0
                                                    ? match.partner_teams.join(", ")
                                                    : <span className="italic opacity-60">Solo</span>
                                                }
                                            </div>
                                        </TableCell>

                                        {/* Opponents */}
                                        <TableCell className="text-[11px]">
                                            <div className={cn(
                                                "flex flex-wrap gap-1 px-2 py-0.5 rounded",
                                                isRed
                                                    ? "bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300"
                                                    : "bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-300"
                                            )}>
                                                {(match.opponent_teams ?? []).join(", ")}
                                            </div>
                                        </TableCell>

                                        {/* Video */}
                                        <TableCell className="text-right">
                                            {match.video_url ? (
                                                <Button variant="ghost" size="sm" asChild className="h-8 w-8 p-0">
                                                    <Link href={match.video_url} target="_blank">
                                                        <Video className="h-4 w-4 text-primary" />
                                                    </Link>
                                                </Button>
                                            ) : (
                                                <span className="text-muted-foreground text-[10px] italic">—</span>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </div>
            </div>
        </Card>
    );
}

function formatDateRange(start: string, end?: string): string {
    const s = new Date(start);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const startStr = `${months[s.getMonth()]} ${s.getDate()}`;

    if (!end || start === end) {
        return `${startStr}, ${s.getFullYear()}`;
    }

    const e = new Date(end);
    if (s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()) {
        return `${months[s.getMonth()]} ${s.getDate()}-${e.getDate()}, ${s.getFullYear()}`;
    }

    if (s.getFullYear() === e.getFullYear()) {
        return `${months[s.getMonth()]} ${s.getDate()} - ${months[e.getMonth()]} ${e.getDate()}, ${s.getFullYear()}`;
    }

    return `${startStr}, ${s.getFullYear()} - ${months[e.getMonth()]} ${e.getDate()}, ${e.getFullYear()}`;
}
