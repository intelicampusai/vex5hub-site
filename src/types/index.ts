export interface Team {
    id: number;
    number: string;
    name: string;
    robot_name?: string;
    organization: string;
    grade: 'High School' | 'Middle School' | 'College';
    region: string;
    country: string;
    worlds_qualified?: boolean;
    stats?: {
        rank: number;
        wins: number;
        losses: number;
        ties: number;
        wp: number;
        ap: number;
        sp: number;
        total_matches: number;
    };
    skills?: {
        driver_score: number;
        programming_score: number;
        combined_score: number;
        rank: number;
    };
}

export interface Event {
    id?: number;
    sku: string;
    name: string;
    start: string;
    end: string;
    season_id?: number;
    location: {
        venue: string;
        city: string;
        region: string;
        country?: string;
    };
    capacity?: {
        max: number;
        current: number;
    };
    division_ids?: number[];
    status: 'active' | 'future' | 'past';
    livestream_url?: string;
    grade?: string;
}

export interface Match {
    id: number;
    event_id: number;
    division_id: number;
    round: number;
    instance: number;
    matchnum: number;
    scheduled: string;
    started?: string;
    field?: string;
    name?: string;
    alliances: {
        red: { score: number; teams: { team: { id: number; name: string } }[] };
        blue: { score: number; teams: { team: { id: number; name: string } }[] };
    };
    video_url?: string;
    event?: {
        id: number;
        name: string;
        sku?: string;
    };
}
