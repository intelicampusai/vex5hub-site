'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    ExternalLink, Youtube, MessageCircle, Globe, Newspaper,
    Trophy, Wrench, Users, Flame, Filter
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// ── Types ──────────────────────────────────────────────
type Source = 'youtube' | 'reddit' | 'vexforum' | 'official' | 'news';
type Category = 'trending' | 'worlds' | 'builds' | 'community' | 'official';

interface ContentItem {
    title: string;
    description: string;
    url: string;
    source: Source;
    category: Category[];
    date: string;        // ISO date
    author?: string;
    hot?: boolean;       // extra emphasis
}

// ── Source Config ───────────────────────────────────────
const SOURCE_CONFIG: Record<Source, { label: string; color: string; icon: typeof Globe }> = {
    youtube:  { label: 'YouTube',   color: 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-800',         icon: Youtube },
    reddit:   { label: 'Reddit',    color: 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-800', icon: MessageCircle },
    vexforum: { label: 'VEX Forum', color: 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800',   icon: MessageCircle },
    official: { label: 'Official',  color: 'bg-green-100 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-300 dark:border-green-800', icon: Globe },
    news:     { label: 'News',      color: 'bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-300 dark:border-purple-800', icon: Newspaper },
};

const CATEGORY_CONFIG: { key: Category | 'all'; label: string; icon: typeof Globe }[] = [
    { key: 'all',       label: 'All',              icon: Filter },
    { key: 'trending',  label: 'Trending',         icon: Flame },
    { key: 'worlds',    label: 'Worlds Prep',      icon: Trophy },
    { key: 'builds',    label: 'Builds & Strategy', icon: Wrench },
    { key: 'community', label: 'Community',        icon: Users },
    { key: 'official',  label: 'Official',         icon: Globe },
];

// ── Curated Content ────────────────────────────────────
const CONTENT: ContentItem[] = [
    // ── WORLDS ──
    {
        title: "2026 VEX Worlds: Everything You Need to Know",
        description: "Complete guide to the 2026 VEX Robotics World Championship in St. Louis (Apr 21-30). HS Apr 21-24, MS Apr 25-27. Registration payment deadline: March 31.",
        url: "https://www.robotevents.com/robot-competitions/vex-robotics-competition/RE-V5RC-26-4025.html",
        source: "official",
        category: ["worlds", "trending"],
        date: "2026-03-13",
        hot: true,
    },
    {
        title: "RECF Worlds Newsletter: Release Forms, Robot Shipping & Logistics",
        description: "Critical info for Worlds-bound teams: participant release forms, visa letters, meal vouchers, robot shipping (must arrive by Apr 20), and lodging through Orchid Events.",
        url: "https://www.roboticseducation.org/",
        source: "official",
        category: ["worlds", "official"],
        date: "2026-03-13",
    },
    {
        title: "Worlds Waitlist Invitations Now Open",
        description: "Random selections happening every Wednesday starting March 18. Check RobotEvents for your team's status. ERCs concluded March 15 — final qualification window closed.",
        url: "https://www.robotevents.com/",
        source: "official",
        category: ["worlds", "trending"],
        date: "2026-03-18",
        hot: true,
    },
    {
        title: "Coach Academy Office Hours & Webinar for Worlds",
        description: "Coaches preparing for Worlds can attend office hours on March 23 and a training webinar on March 25 hosted by the REC Foundation.",
        url: "https://www.roboticseducation.org/",
        source: "official",
        category: ["worlds", "official"],
        date: "2026-03-12",
    },
    // ── COMMUNITY / NEWS ──
    {
        title: "Sherrard MS Teams Win West Virginia State Championship, Head to Worlds",
        description: "An alliance of Sherrard Middle School robotics teams captured the WV state championship and will compete at the VEX World Robotics Championship in April.",
        url: "https://www.theintelligencer.net/",
        source: "news",
        category: ["community", "trending"],
        date: "2026-03-10",
        hot: true,
    },
    {
        title: "Lynx Robotics Crowned 2026 State Tournament Champions",
        description: "Lynx Robotics earned the State Tournament Championship title and secured their spot at the 2026 VEX Worlds in St. Louis.",
        url: "https://www.alechoes.com/",
        source: "news",
        category: ["community", "worlds"],
        date: "2026-03-08",
    },
    {
        title: "Frazer School Sends 7 Teams to VEX Worlds",
        description: "Two elementary and five middle school teams from Frazer School qualified for the World Championship through strong performances at regional competitions.",
        url: "https://mainstreetdailynews.com/",
        source: "news",
        category: ["community", "worlds"],
        date: "2026-03-06",
    },
    // ── BUILDS & STRATEGY ──
    {
        title: "Push Back Game Reveal — Official VEX Robotics",
        description: "The official 2025-2026 V5RC game 'Push Back' reveal. Score blocks into goals, control zones, and park robots. 88 blocks, 4 goals, 15s auton + 1:45 driver.",
        url: "https://www.youtube.com/watch?v=VEX_PushBack_Reveal",
        source: "youtube",
        category: ["builds", "official"],
        date: "2025-06-03",
        author: "VEX Robotics",
    },
    {
        title: "High-Scoring Autonomous Routines for Push Back",
        description: "Community breakdown of the best autonomous strategies being used at state championships. Covers multi-block scoring paths and zone control timing.",
        url: "https://www.reddit.com/r/vex_robotics/",
        source: "reddit",
        category: ["builds", "trending"],
        date: "2026-02-28",
    },
    {
        title: "Push Back Meta: What the Top Teams Are Running",
        description: "Analysis of robot designs dominating at regionals and states — claw vs intake, defensive strategies, and the importance of consistent auton.",
        url: "https://www.vexforum.com/",
        source: "vexforum",
        category: ["builds", "community"],
        date: "2026-03-02",
    },
    {
        title: "3D Printing & Custom Plastics Rule Clarification",
        description: "Official Q&A ruling on the use of custom plastics, 3D printed decorations, and license plates for the 2025-2026 season. Key reading before Worlds.",
        url: "https://www.robotevents.com/",
        source: "official",
        category: ["builds", "official"],
        date: "2026-02-15",
    },
    // ── COMMUNITY DISCUSSIONS ──
    {
        title: "How Are Teams Preparing for Worlds? Share Your Plans",
        description: "Active Reddit thread where teams share their preparation strategies, practice schedules, and last-minute design changes heading into the World Championship.",
        url: "https://www.reddit.com/r/vex_robotics/",
        source: "reddit",
        category: ["community", "worlds"],
        date: "2026-03-11",
    },
    {
        title: "State Championship Results Megathread",
        description: "Compilation of state championship results from across the US and Canada. Teams share their wins, upsets, and qualification stories.",
        url: "https://www.reddit.com/r/vex_robotics/",
        source: "reddit",
        category: ["community", "trending"],
        date: "2026-03-09",
        hot: true,
    },
    {
        title: "Tips for First-Time Worlds Attendees",
        description: "Veteran teams share advice on navigating the VEX World Championship — pit setup tips, schedule management, judging preparation, and what to expect in St. Louis.",
        url: "https://www.vexforum.com/",
        source: "vexforum",
        category: ["community", "worlds"],
        date: "2026-03-05",
    },
    {
        title: "World Rankings Discussion: Who's the Team to Beat?",
        description: "Community debate on which teams are looking strongest heading into Worlds based on skills scores, win rates, and recent competition performances.",
        url: "https://www.reddit.com/r/vex_robotics/",
        source: "reddit",
        category: ["community", "trending"],
        date: "2026-03-14",
    },
    // ── OFFICIAL ──
    {
        title: "2025-2026 Season Calendar & Key Deadlines",
        description: "Complete season calendar from the REC Foundation with competition registration deadlines, qualification cutoffs, and Worlds milestones.",
        url: "https://recf.org/vex-robotics/competition-calendar/",
        source: "official",
        category: ["official"],
        date: "2025-08-01",
    },
    {
        title: "Engineering Notebook Submission Open for Worlds",
        description: "All Worlds-qualified teams can now submit their digital engineering notebook links. Remote judging interviews must be completed to be considered for judged awards.",
        url: "https://www.roboticseducation.org/",
        source: "official",
        category: ["official", "worlds"],
        date: "2026-03-13",
    },
];

// ── Component ──────────────────────────────────────────
export default function LibraryPage() {
    const [selectedCategory, setSelectedCategory] = useState<Category | 'all'>('all');
    const [selectedSource, setSelectedSource] = useState<Source | 'all'>('all');

    const filtered = CONTENT
        .filter(item => selectedCategory === 'all' || item.category.includes(selectedCategory))
        .filter(item => selectedSource === 'all' || item.source === selectedSource)
        .sort((a, b) => {
            // Hot items first, then by date descending
            if (a.hot && !b.hot) return -1;
            if (b.hot && !a.hot) return 1;
            return new Date(b.date).getTime() - new Date(a.date).getTime();
        })
        .slice(0, 9); // Only show the latest 9 items

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Library</h1>
                <p className="text-sm text-muted-foreground mt-1">
                    Curated VEX V5RC news, community highlights, and team updates from across the web.
                </p>
            </div>

            {/* Filters */}
            <div className="space-y-3 bg-muted/30 p-4 rounded-xl border">
                {/* Category tabs */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
                    {CATEGORY_CONFIG.map(({ key, label, icon: Icon }) => (
                        <Button
                            key={key}
                            variant={selectedCategory === key ? "default" : "outline"}
                            size="sm"
                            className="whitespace-nowrap px-3 h-8 text-[11px] rounded-full gap-1.5"
                            onClick={() => setSelectedCategory(key)}
                        >
                            <Icon className="h-3 w-3" />
                            {label}
                        </Button>
                    ))}
                </div>

                {/* Source tabs */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
                    <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mr-1 shrink-0">Source:</span>
                    <Button
                        variant={selectedSource === 'all' ? "default" : "outline"}
                        size="sm"
                        className="whitespace-nowrap px-3 h-7 text-[11px] rounded-full"
                        onClick={() => setSelectedSource('all')}
                    >
                        All
                    </Button>
                    {(Object.keys(SOURCE_CONFIG) as Source[]).map(src => {
                        const { label, icon: Icon } = SOURCE_CONFIG[src];
                        return (
                            <Button
                                key={src}
                                variant={selectedSource === src ? "default" : "outline"}
                                size="sm"
                                className="whitespace-nowrap px-3 h-7 text-[11px] rounded-full gap-1"
                                onClick={() => setSelectedSource(src)}
                            >
                                <Icon className="h-3 w-3" />
                                {label}
                            </Button>
                        );
                    })}
                </div>
            </div>

            {/* Results count */}
            <p className="text-xs text-muted-foreground">
                Showing the latest {filtered.length} item{filtered.length !== 1 ? 's' : ''}
            </p>

            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map((item, i) => (
                    <ContentCard key={i} item={item} />
                ))}
            </div>

            {filtered.length === 0 && (
                <div className="text-center py-12 text-muted-foreground text-sm border rounded-lg border-dashed">
                    No content found for this filter combination.
                </div>
            )}
        </div>
    );
}

function ContentCard({ item }: { item: ContentItem }) {
    const src = SOURCE_CONFIG[item.source];
    const SrcIcon = src.icon;
    const dateStr = new Date(item.date).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric'
    });

    return (
        <Link href={item.url} target="_blank" rel="noopener noreferrer">
            <Card className={cn(
                "h-full hover:border-primary/50 transition-all hover:shadow-md group cursor-pointer",
                item.hot && "border-amber-300/50 dark:border-amber-700/50"
            )}>
                {item.hot && (
                    <div className="h-1 bg-gradient-to-r from-amber-400 via-orange-500 to-red-500 rounded-t-lg" />
                )}
                <CardHeader className="pb-2">
                    <div className="flex items-center gap-1.5 flex-wrap mb-1.5">
                        {item.hot && (
                            <Badge className="bg-amber-500 text-white text-[10px] px-1.5 py-0 h-4 gap-0.5">
                                <Flame className="h-2.5 w-2.5" /> HOT
                            </Badge>
                        )}
                        <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0 h-4 gap-0.5", src.color)}>
                            <SrcIcon className="h-2.5 w-2.5" />
                            {src.label}
                        </Badge>
                        {item.category.map(cat => {
                            const cfg = CATEGORY_CONFIG.find(c => c.key === cat);
                            if (!cfg || cat === 'trending') return null;
                            return (
                                <Badge key={cat} variant="outline" className="text-[10px] px-1.5 py-0 h-4">
                                    {cfg.label}
                                </Badge>
                            );
                        })}
                    </div>
                    <CardTitle className="text-sm font-semibold leading-tight line-clamp-2 group-hover:text-primary transition-colors">
                        {item.title}
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 pb-3">
                    <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                        {item.description}
                    </p>
                    <div className="flex items-center justify-between pt-1 border-t">
                        <span className="text-[10px] text-muted-foreground">
                            {item.author ? `${item.author} · ` : ''}{dateStr}
                        </span>
                        <ExternalLink className="h-3 w-3 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                </CardContent>
            </Card>
        </Link>
    );
}
