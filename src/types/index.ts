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
    /** Sort key: MATCH#{sku}#{div_id}#{match_num:04d} */
    SK: string;
    sku: string;
    event_name: string;
    division_id: number;
    match_num: number;
    round: string;       // 'Practice' | 'Qualification' | 'Quarterfinal' | 'Semifinal' | 'Final' | 'Round of 16'
    alliance: 'red' | 'blue';
    partner_teams: string[];
    opponent_teams: string[];
    my_score?: number;
    opp_score?: number;
    won?: boolean;
    scheduled?: string;
    updated_at?: string;
    video_url?: string;
    event_start?: string;
    event_end?: string;
    event_location?: string;
}
