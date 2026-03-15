'use client';

import { useEffect, useState } from 'react';
import { TeamCard } from "@/components/dashboard/TeamCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Calendar, MapPin, Users, Video, ExternalLink, RefreshCw } from "lucide-react";
import Link from "next/link";
import { Team, Event } from "@/types";
import { cn } from "@/lib/utils";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
const SEASON_ID = process.env.NEXT_PUBLIC_SEASON_ID || "197";

async function fetchLive<T>(path: string): Promise<T | null> {
    if (!API_URL) return null;
    try {
        const res = await fetch(`${API_URL}${path}`, { cache: 'no-store' });
        if (!res.ok) return null;
        return res.json();
    } catch { return null; }
}

function mapEvent(item: any): Event {
    return {
        id: item.id,
        sku: item.sku,
        name: item.name,
        start: item.start,
        end: item.end,
        season_id: item.season_id,
        location: item.location || {},
        capacity: item.capacity,
        division_ids: item.division_ids,
        status: item.status || 'future',
        livestream_url: item.livestream_url,
        grade: item.grade_level || item.grade,
        level: item.level || 'Other',
        match_count: item.match_count,
    };
}

export default function Home() {
    const [teams, setTeams] = useState<Team[]>([]);
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            const [rawTeams, rawEvents] = await Promise.all([
                fetchLive<Team[]>(`/teams?season=${SEASON_ID}`),
                fetchLive<any[]>(`/events?season=${SEASON_ID}`),
            ]);
            if (rawTeams) setTeams(rawTeams.slice(0, 4));
            if (rawEvents) {
                const mapped = rawEvents.map(mapEvent);
                // Sort: active first, then future by start date, filter out past
                const splitPoint = new Date(Date.now() - 12 * 60 * 60 * 1000);
                const upcoming = mapped
                    .filter(e => new Date(e.end) >= splitPoint)
                    .sort((a, b) => {
                        if (a.status === 'active' && b.status !== 'active') return -1;
                        if (b.status === 'active' && a.status !== 'active') return 1;
                        return new Date(a.start).getTime() - new Date(b.start).getTime();
                    });
                setEvents(upcoming.slice(0, 3));
            }
            setLoading(false);
        };
        load();
    }, []);

    return (
        <div className="space-y-8">
            {/* Happening Now / Upcoming */}
            <section className="space-y-3">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold tracking-tight flex items-center gap-2">
                        <Calendar className="h-5 w-5 text-primary" />
                        Upcoming Events
                    </h2>
                    <Link href="/events" className="text-sm text-primary flex items-center gap-1 hover:underline">
                        View All <ArrowRight className="h-3 w-3" />
                    </Link>
                </div>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-40 bg-muted animate-pulse rounded-lg" />
                        ))}
                    </div>
                ) : events.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {events.map(event => (
                            <HomeEventCard key={event.sku} event={event} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-muted-foreground text-sm border rounded-lg">
                        No upcoming events found.
                    </div>
                )}
            </section>

            {/* Top Performers */}
            <section className="space-y-3">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold tracking-tight">Top Performers</h2>
                    <Link href="/teams" className="text-sm text-primary flex items-center gap-1 hover:underline">
                        Rankings <ArrowRight className="h-3 w-3" />
                    </Link>
                </div>

                {loading ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-36 bg-muted animate-pulse rounded-lg" />
                        ))}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                        {teams.map(team => (
                            <TeamCard key={team.number} team={team} />
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}

function HomeEventCard({ event }: { event: Event }) {
    const isLive = event.status === 'active';
    const startDate = new Date(event.start).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
    });
    const eventUrl = event.sku
        ? `https://www.robotevents.com/robot-competitions/vex-robotics-competition/${event.sku}.html`
        : null;

    return (
        <Card className={cn(
            "overflow-hidden group hover:border-primary/50 transition-all hover:shadow-md",
            isLive && "border-green-500/50 shadow-green-500/10 shadow-md"
        )}>
            {isLive && (
                <div className="h-1 bg-gradient-to-r from-green-400 to-emerald-500" />
            )}
            <CardHeader className="pb-2">
                <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    {isLive && (
                        <Badge className="bg-green-500 text-white text-[10px] px-1.5 py-0 h-4 animate-pulse">
                            LIVE
                        </Badge>
                    )}
                    {event.level && event.level !== 'Other' && (
                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4 bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300">
                            {event.level}
                        </Badge>
                    )}
                    {event.grade && (
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                            {event.grade.replace('High School', 'HS').replace('Middle School', 'MS')}
                        </Badge>
                    )}
                </div>
                <CardTitle className="text-sm font-semibold leading-tight line-clamp-2 group-hover:text-primary transition-colors">
                    {event.name}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 pb-3">
                <div className="flex items-center text-xs text-muted-foreground gap-1.5">
                    <Calendar className="h-3.5 w-3.5 shrink-0" />
                    <span>{startDate}</span>
                </div>
                <div className="flex items-center text-xs text-muted-foreground gap-1.5">
                    <MapPin className="h-3.5 w-3.5 shrink-0" />
                    <span className="line-clamp-1">
                        {[event.location?.city, event.location?.region].filter(Boolean).join(', ')}
                    </span>
                </div>
                <div className="flex items-center justify-between pt-1 border-t">
                    {event.capacity ? (
                        <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {event.capacity.current}/{event.capacity.max} Teams
                        </span>
                    ) : (
                        <span />
                    )}
                    {eventUrl && (
                        <Link
                            href={eventUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-muted-foreground hover:text-primary flex items-center gap-0.5"
                        >
                            RobotEvents <ExternalLink className="h-3 w-3" />
                        </Link>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
