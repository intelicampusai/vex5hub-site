'use client';

import React, { useState } from 'react';
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
    Users
} from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';

interface EventsClientProps {
    initialEvents: Event[];
    topRegions?: string[];
}

export default function EventsClient({ initialEvents, topRegions = [] }: EventsClientProps) {
    const [selectedRegion, setSelectedRegion] = useState<string>('All Regions');

    const [searchQuery, setSearchQuery] = useState('');
    const [expandedUpcoming, setExpandedUpcoming] = useState(true);
    const [expandedPast, setExpandedPast] = useState(false);

    // Sort: topRegions first (competitiveness), then other event regions sorted alphabetically
    const topRegionsSet = new Set(topRegions);
    const eventRegions = Array.from(new Set(initialEvents.map(e => e.location.region)))
        .filter(r => r && !topRegionsSet.has(r))
        .sort();

    const regions = ['All Regions', ...topRegions, ...eventRegions];

    // Filter events
    const filteredEvents = initialEvents.filter(event => {
        const matchesRegion = selectedRegion === 'All Regions' || event.location.region === selectedRegion;
        const matchesSearch = event.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            event.location.city.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesRegion && matchesSearch;
    });

    // Current time for splitting
    const now = new Date();

    const upcomingEvents = filteredEvents.filter(e => new Date(e.end) >= now)
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

    const pastEvents = filteredEvents.filter(e => new Date(e.end) < now)
        .sort((a, b) => new Date(b.start).getTime() - new Date(a.start).getTime());

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-muted/30 p-4 rounded-xl border">
                <div className="relative w-full md:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search events..."
                        className="pl-9 bg-background"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="flex items-center space-x-2 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
                    <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="flex space-x-2">
                        {regions.map(region => (
                            <Button
                                key={region}
                                variant={selectedRegion === region ? "default" : "outline"}
                                size="sm"
                                className="whitespace-nowrap px-3 h-8 text-xs rounded-full"
                                onClick={() => setSelectedRegion(region)}
                            >
                                {region}
                            </Button>
                        ))}
                    </div>
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
                    <div className="flex items-center text-xs text-muted-foreground">
                        <Users className="h-3.5 w-3.5 mr-1" />
                        <span>{event.capacity ? `${event.capacity.current}/${event.capacity.max}` : "N/A"} Teams</span>
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
