'use client';

import React, { useState, useEffect } from 'react';
import { Event } from '@/types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Calendar,
    MapPin,
    ChevronDown,
    ChevronUp,
    Filter,
    Search,
    Video,
    Users,
    RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

interface EventsClientProps {
    initialEvents: Event[];
    topRegions?: string[];
}

// Season ID for API calls (2025-2026 season)
const SEASON_ID = process.env.NEXT_PUBLIC_SEASON_ID || "197";

export default function EventsClient({ initialEvents, topRegions = [] }: EventsClientProps) {
    const [events, setEvents] = useState<Event[]>(initialEvents);
    const [isLoading, setIsLoading] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [selectedLevel, setSelectedLevel] = useState<string>('All');
    const [selectedCountry, setSelectedCountry] = useState<string>('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [expandedUpcoming, setExpandedUpcoming] = useState(true);
    const [expandedPast, setExpandedPast] = useState(false);

    // Fetch fresh events data from API
    const fetchFreshEvents = async () => {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!apiUrl) return;

        setIsLoading(true);
        try {
            const response = await fetch(`${apiUrl}/events?season=${SEASON_ID}`, {
                cache: 'no-store'
            });
            if (response.ok) {
                const data = await response.json();
                if (Array.isArray(data)) {
                    const formattedEvents = data.map((item: any) => ({
                        id: item.id,
                        sku: item.sku,
                        name: item.name,
                        start: item.start,
                        end: item.end,
                        season_id: item.season_id,
                        location: item.location,
                        capacity: item.capacity,
                        division_ids: item.division_ids,
                        status: item.status || 'future',
                        livestream_url: item.livestream_url,
                        grade: item.grade_level || item.grade,
                        level: item.level || 'Other',
                        match_count: item.match_count
                    }));
                    setEvents(formattedEvents);
                    setLastRefresh(new Date());
                }
            }
        } catch (error) {
            console.error('Failed to fetch fresh events:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch fresh data on initial mount
    useEffect(() => {
        fetchFreshEvents();
    }, []);

    // Filter Options
    const levelOptions = ['All', 'Signature', 'Regional', 'National', 'World'];
    const countryOptions = ['All', 'United States', 'China', 'Canada', 'Australia', 'Europe'];

    // Filter events
    const filteredEvents = events.filter(event => {
        // Search filter (High priority)
        const searchLower = searchQuery.toLowerCase();
        const matchesSearch = !searchQuery ||
            event.name.toLowerCase().includes(searchLower) ||
            event.location.city.toLowerCase().includes(searchLower) ||
            event.sku.toLowerCase().includes(searchLower);

        // If search query is used, we often want it to be broad, but here let's combine it
        if (searchQuery && !matchesSearch) return false;

        // Level filtering
        const matchesLevel = selectedLevel === 'All' ||
            (event.level === selectedLevel) ||
            (selectedLevel === 'Regional' && event.name.includes('Region')) ||
            (selectedLevel === 'National' && event.name.includes('National')) ||
            (selectedLevel === 'World' && event.name.includes('World'));

        // Country filtering
        const matchesCountry = selectedCountry === 'All' ||
            event.location.country === selectedCountry ||
            (selectedCountry === 'United States' && (event.location.country === 'USA' || event.location.country === 'US' || event.location.country === 'United States'));

        return matchesLevel && matchesCountry;
    });

    // Current split point: 12 hours ago to catch currently active events
    const splitPoint = new Date(new Date().getTime() - 12 * 60 * 60 * 1000);

    const upcomingEvents = filteredEvents.filter(e => new Date(e.end) >= splitPoint)
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

    const pastEvents = filteredEvents.filter(e => new Date(e.end) < splitPoint)
        .sort((a, b) => new Date(b.start).getTime() - new Date(a.start).getTime());

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 bg-muted/30 p-4 rounded-xl border">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="relative w-full md:w-72">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search by SKU or name..."
                            className="pl-9 bg-background"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-2">
                        {lastRefresh && (
                            <span className="text-xs text-muted-foreground">
                                Updated {lastRefresh.toLocaleTimeString()}
                            </span>
                        )}
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={fetchFreshEvents}
                            disabled={isLoading}
                            className="h-8"
                        >
                            <RefreshCw className={cn("h-3.5 w-3.5 mr-1", isLoading && "animate-spin")} />
                            Refresh
                        </Button>
                    </div>

                    <div className="flex items-center space-x-2 w-full md:w-auto p-1 overflow-x-auto pb-1 md:pb-0 scrollbar-hide">
                        <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
                        <div className="flex space-x-1">
                            {countryOptions.map(country => (
                                <Button
                                    key={country}
                                    variant={selectedCountry === country ? "default" : "outline"}
                                    size="sm"
                                    className="whitespace-nowrap px-3 h-8 text-[11px] rounded-full"
                                    onClick={() => setSelectedCountry(country)}
                                >
                                    {country}
                                </Button>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mr-2">Levels:</span>
                    {levelOptions.map(level => (
                        <Button
                            key={level}
                            variant={selectedLevel === level ? "default" : "outline"}
                            size="sm"
                            className="whitespace-nowrap px-3 h-8 text-[11px] rounded-full"
                            onClick={() => setSelectedLevel(level)}
                        >
                            {level === 'Regional' ? 'Region Championship' :
                                level === 'National' ? 'National Championship' :
                                    level === 'World' ? 'World Championship' : level}
                        </Button>
                    ))}
                </div>
            </div>

            {/* Upcoming Events Section */}
            <div className="space-y-4">
                <button
                    onClick={() => setExpandedUpcoming(!expandedUpcoming)}
                    className="w-full flex items-center justify-between p-2 hover:bg-muted/50 rounded-lg transition-colors group"
                >
                    <div className="flex items-center space-x-2">
                        <Calendar className="h-5 w-5 text-primary" />
                        <h2 className="text-xl font-bold tracking-tight">Upcoming Events</h2>
                        <Badge variant="secondary" className="ml-2">{upcomingEvents.length}</Badge>
                    </div>
                    {expandedUpcoming ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
                </button>

                {expandedUpcoming && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {upcomingEvents.length > 0 ? (
                            upcomingEvents.map(event => <EventCard key={event.sku} event={event} />)
                        ) : (
                            <p className="text-muted-foreground italic col-span-full py-8 text-center bg-muted/10 rounded-xl border border-dashed">
                                No upcoming events found.
                            </p>
                        )}
                    </div>
                )}
            </div>

            <div className="h-px bg-border" />

            {/* Past Events Section */}
            <div className="space-y-4">
                <button
                    onClick={() => setExpandedPast(!expandedPast)}
                    className="w-full flex items-center justify-between p-2 hover:bg-muted/50 rounded-lg transition-colors group"
                >
                    <div className="flex items-center space-x-2">
                        <Calendar className="h-5 w-5 text-muted-foreground" />
                        <h2 className="text-xl font-bold tracking-tight text-muted-foreground">Past Events</h2>
                        <Badge variant="outline" className="ml-2 text-muted-foreground">{pastEvents.length}</Badge>
                    </div>
                    {expandedPast ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
                </button>

                {expandedPast && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 opacity-80">
                        {pastEvents.length > 0 ? (
                            pastEvents.map(event => <EventCard key={event.sku} event={event} isPast />)
                        ) : (
                            <p className="text-muted-foreground italic col-span-full py-8 text-center">
                                No past events found.
                            </p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function EventCard({ event, isPast }: { event: Event; isPast?: boolean }) {
    const startDate = new Date(event.start);
    const dateStr = startDate.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });

    return (
        <Card className={cn("overflow-hidden group hover:border-primary/50 transition-all hover:shadow-md", isPast && "grayscale-[0.5]")}>
            <CardHeader className="pb-3 relative">
                <div className="flex justify-between items-start mb-2">
                    <Badge variant={isPast ? "outline" : "default"} className="font-mono text-[10px] uppercase">
                        {event.sku.split('-')[1] || 'VRC'}
                    </Badge>
                    {event.grade && (
                        <Badge variant="outline" className="ml-2 font-mono text-[10px] uppercase">
                            {event.grade.replace('High School', 'HS').replace('Middle School', 'MS').replace('College', 'VU').replace('Elementary School', 'ES')}
                        </Badge>
                    )}
                    {event.level && event.level !== 'Other' && (
                        <Badge variant="secondary" className="ml-2 font-mono text-[10px] uppercase bg-amber-100 text-amber-700 hover:bg-amber-100 border-amber-200">
                            {event.level}
                        </Badge>
                    )}
                    {event.livestream_url && !isPast && (
                        <div className="flex items-center text-[10px] text-red-500 font-bold animate-pulse ml-auto">
                            <Video className="h-3 w-3 mr-1" /> LIVE
                        </div>
                    )}
                </div>
                <CardTitle className="text-base line-clamp-2 min-h-[40px] group-hover:text-primary transition-colors">
                    {event.name}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 pb-4">
                <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4 mr-2 shrink-0 text-primary/70" />
                    <span>{dateStr}</span>
                </div>
                <div className="flex items-start text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4 mr-2 shrink-0 mt-0.5 text-primary/70" />
                    <span className="line-clamp-1">{event.location.city}, {event.location.region}</span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t mt-2">
                    <div className="flex flex-col space-y-1">
                        <div className="flex items-center text-xs text-muted-foreground">
                            <Users className="h-3.5 w-3.5 mr-1" />
                            <span>{event.capacity ? `${event.capacity.current}/${event.capacity.max}` : "N/A"} Teams</span>
                        </div>
                        {event.match_count && event.match_count > 0 && (
                            <div className="flex items-center text-xs text-amber-600 font-medium">
                                <Search className="h-3.5 w-3.5 mr-1" />
                                <span>{event.match_count} Matches</span>
                            </div>
                        )}
                    </div>
                    <Button variant="ghost" size="sm" className="h-7 text-xs px-2" asChild>
                        <Link
                            href={`https://www.robotevents.com/robot-competitions/vex-robotics-competition/${event.sku.replace('RE-VRC-25', 'RE-V5RC-25')}.html#general-info`}
                            target="_blank"
                        >
                            View RE
                        </Link>
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
