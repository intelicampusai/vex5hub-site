import { Team, Event, Match } from '@/types';

// RobotEvents Season IDs
export const SEASON_ID = process.env.NEXT_PUBLIC_SEASON_ID || "197";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

async function fetchFromApi<T>(path: string): Promise<T | null> {
    if (!API_BASE_URL) return null;
    try {
        const headers: HeadersInit = {
            'Accept': 'application/json',
        };
        const token = process.env.ROBOTEVENTS_TOKEN;
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE_URL}${path}`, {
            headers,
            next: { revalidate: 3600 } // Cache for 1 hour
        });
        if (!response.ok) return null;

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.error(`API Error: Expected JSON but got ${contentType} for ${path}`);
            return null;
        }

        return response.json();
    } catch (error) {
        console.error(`API Fetch Error (${path}):`, error);
        return null;
    }
}
const MOCK_TEAMS: Team[] = [
    {
        "id": 13212,
        "number": "13212D",
        "name": "SixSeven",
        "organization": "Concordia International School Shanghai",
        "grade": "High School",
        "region": "Shanghai",
        "country": "China",
        "stats": {
            "rank": 1,
            "wins": 0, "losses": 0, "ties": 0, "wp": 0, "ap": 0, "sp": 0,
            "total_matches": 0
        },
        "skills": {
            "driver_score": 119,
            "programming_score": 100,
            "combined_score": 219,
            "rank": 1
        }
    },
    {
        "id": 3588,
        "number": "3588Y",
        "name": "Cyber Spacers",
        "organization": "Edubot Inc.",
        "grade": "Middle School",
        "region": "California",
        "country": "United States",
        "stats": {
            "rank": 1,
            "wins": 0, "losses": 0, "ties": 0, "wp": 0, "ap": 0, "sp": 0,
            "total_matches": 0
        },
        "skills": {
            "driver_score": 116,
            "programming_score": 113,
            "combined_score": 229,
            "rank": 1
        }
    },
    {
        "id": 3150,
        "number": "3150N",
        "name": "Nighthawks",
        "organization": "Ridley College",
        "grade": "Middle School",
        "region": "Ontario",
        "country": "Canada",
        "stats": {
            "rank": 12,
            "wins": 0, "losses": 0, "ties": 0, "wp": 0, "ap": 0, "sp": 0,
            "total_matches": 0
        },
        "skills": {
            "driver_score": 102,
            "programming_score": 90,
            "combined_score": 192,
            "rank": 12
        }
    },
    {
        "id": 1590,
        "number": "1590A",
        "name": "Blue Army",
        "organization": "Innovagine Robotics",
        "grade": "Middle School",
        "region": "California",
        "country": "United States",
        "stats": {
            "rank": 2,
            "wins": 0, "losses": 0, "ties": 0, "wp": 0, "ap": 0, "sp": 0,
            "total_matches": 0
        },
        "skills": {
            "driver_score": 101,
            "programming_score": 88,
            "combined_score": 189,
            "rank": 2
        }
    },
    {
        "id": 3589,
        "number": "3588X",
        "name": "Galaxy",
        "organization": "Edubot Inc.",
        "grade": "High School",
        "region": "California",
        "country": "United States",
        "stats": {
            "rank": 2,
            "wins": 0, "losses": 0, "ties": 0, "wp": 0, "ap": 0, "sp": 0,
            "total_matches": 0
        },
        "skills": {
            "driver_score": 115,
            "programming_score": 102,
            "combined_score": 217,
            "rank": 2
        }
    }
];

const MOCK_EVENTS: Event[] = [
    {
        id: 1,
        sku: 'RE-V5RC-25-1234',
        name: 'Ontario Provincial Championship',
        start: '2026-02-28T08:00:00Z',
        end: '2026-03-01T17:00:00Z',
        season_id: 197,
        location: { venue: 'The International Centre', city: 'Mississauga', region: 'Ontario' },
        capacity: { max: 80, current: 80 },
        division_ids: [1],
        status: 'future',
        grade: 'High School'
    },
    {
        id: 2,
        sku: 'RE-V5RC-25-5678',
        name: 'Ridley College Signature Event',
        start: '2026-02-14T08:00:00Z',
        end: '2026-02-14T17:00:00Z',
        season_id: 197,
        location: { venue: 'Ridley College', city: 'St. Catharines', region: 'Ontario' },
        capacity: { max: 40, current: 32 },
        division_ids: [1],
        status: 'active',
        livestream_url: 'https://youtube.com/live/example',
        grade: 'Middle School'
    },
    {
        id: 3,
        sku: 'RE-V5RC-25-9999',
        name: 'California State Championship',
        start: '2026-03-15T08:00:00Z',
        end: '2026-03-16T17:00:00Z',
        season_id: 197,
        location: { venue: 'Santa Clara Convention Center', city: 'Santa Clara', region: 'California' },
        capacity: { max: 100, current: 45 },
        division_ids: [1, 2],
        status: 'future',
        grade: 'High School, Middle School'
    },
    {
        id: 4,
        sku: 'RE-VRC-23-0001',
        name: 'Kalahari Classic (Past)',
        start: '2026-01-21T08:00:00Z',
        end: '2026-01-22T17:00:00Z',
        season_id: 190,
        location: { venue: 'Kalahari Resorts', city: 'Sandusky', region: 'Ohio' },
        capacity: { max: 200, current: 200 },
        division_ids: [1, 2, 3],
        status: 'past',
        grade: 'High School'
    },
    {
        id: 5,
        sku: 'RE-VRC-23-0002',
        name: 'Asia-Pacific Championship (Past)',
        start: '2025-12-10T08:00:00Z',
        end: '2025-12-12T17:00:00Z',
        season_id: 190,
        location: { venue: 'Guangzhou International Center', city: 'Guangzhou', region: 'Guangdong' },
        capacity: { max: 300, current: 300 },
        division_ids: [1, 2, 3, 4],
        status: 'past',
        grade: 'High School, Middle School'
    }
];

const MOCK_MATCHES: Match[] = [
    {
        id: 101,
        event_id: 1,
        division_id: 1,
        round: 2, // Qualification
        instance: 1,
        matchnum: 42,
        scheduled: '2026-02-14T10:15:00Z',
        started: '2026-02-14T10:16:30Z',
        field: 'Main Stage',
        alliances: {
            red: { score: 24, teams: [{ team: { id: 1, name: '3150N' } }, { team: { id: 5, name: '1234A' } }] },
            blue: { score: 12, teams: [{ team: { id: 6, name: '5678B' } }, { team: { id: 7, name: '9999X' } }] }
        },
        video_url: 'https://youtube.com/watch?v=example&t=3600s'
    },
    {
        id: 102,
        event_id: 1,
        division_id: 1,
        round: 2,
        instance: 1,
        matchnum: 58,
        scheduled: '2026-02-14T11:45:00Z',
        started: '2026-02-14T11:50:00Z',
        field: 'Main Stage',
        alliances: {
            red: { score: 10, teams: [{ team: { id: 8, name: '1111A' } }, { team: { id: 9, name: '2222B' } }] },
            blue: { score: 28, teams: [{ team: { id: 1, name: '3150N' } }, { team: { id: 10, name: '3333C' } }] }
        }
    }
];

export async function getTeams(query: string = ''): Promise<Team[]> {
    const apiTeams = await fetchFromApi<Team[]>(`/teams?season=${SEASON_ID}&q=${query}`);
    if (apiTeams) return apiTeams;

    // Simulate API delay for mock
    await new Promise(resolve => setTimeout(resolve, 500));
    if (!query) return MOCK_TEAMS;
    return MOCK_TEAMS.filter(t =>
        t.number.toLowerCase().includes(query.toLowerCase()) ||
        t.name.toLowerCase().includes(query.toLowerCase())
    );
}

export async function getEvents(): Promise<Event[]> {
    let allEvents: Event[] = [];
    let page = 1;
    let lastPage = 1;

    // Loop to fetch all pages
    do {
        // Add a small delay between requests to be nice to the API
        if (page > 1) await new Promise(resolve => setTimeout(resolve, 200));

        const response = await fetchFromApi<any>(`/events?season=${SEASON_ID}&page=${page}`);

        if (!response || !response.data) {
            // If API fails or no data, stop. 
            // If it's the first page and fails, we might want to return mock data?
            if (page === 1 && allEvents.length === 0) break;
            else break;
        }

        if (page === 1 && response.data && response.data.length > 0) {
            // console.log("DEBUG EVENT DATA:", JSON.stringify(response.data[0], null, 2));
        }

        const events = response.data.map((item: any) => ({
            id: item.id,
            sku: item.sku,
            name: item.name,
            start: item.start,
            end: item.end,
            season_id: item.season_id,
            location: item.location,
            capacity: item.capacity,
            division_ids: item.division_ids,
            status: item.status || 'future', // Fallback
            livestream_url: item.livestream_url,
            // Try to find grade level
            grade: item.level || item.grade_level || (item.program ? item.program.grade_level : undefined)
        }));

        allEvents = allEvents.concat(events);

        // RobotEvents API meta structure
        if (response.meta?.last_page) {
            lastPage = response.meta.last_page;
        } else {
            break; // No pagination info
        }

        page++;
    } while (page <= lastPage && page <= 20); // Safety limit of 20 pages

    if (allEvents.length > 0) return allEvents;

    // Fallback to MOCK_EVENTS if simplified API call failed or returned nothing valid
    await new Promise(resolve => setTimeout(resolve, 500));
    return MOCK_EVENTS;
}

export async function getTeam(number: string): Promise<Team | undefined> {
    const apiTeam = await fetchFromApi<Team>(`/teams/${number}`);
    if (apiTeam) return apiTeam;

    await new Promise(resolve => setTimeout(resolve, 500));
    return MOCK_TEAMS.find(t => t.number === number);
}

export async function getMatches(teamNumber: string): Promise<Match[]> {
    const apiTeamDetail = await fetchFromApi<Team & { matches: Match[] }>(`/teams/${teamNumber}`);
    if (apiTeamDetail && apiTeamDetail.matches) return apiTeamDetail.matches;

    await new Promise(resolve => setTimeout(resolve, 500));
    return MOCK_MATCHES.filter(m =>
        m.alliances.red.teams.some(t => t.team.name === teamNumber) ||
        m.alliances.blue.teams.some(t => t.team.name === teamNumber)
    );
}

export async function getSkillsStandings(): Promise<Team[]> {
    // Fetch top 100 skills teams
    const path = `/seasons/${SEASON_ID}/skills?grade_level=Middle%20School&grade_level=High%20School&sort=score&limit=100`;
    const data = await fetchFromApi<any[]>(path);

    if (!data) return MOCK_TEAMS;

    // Transform API response to Team objects if necessary
    // RobotEvents /skills endpoint returns objects with 'team', 'rank', 'score', etc.
    return data.map((item: any) => ({
        id: item.team.id,
        number: item.team.name, // RobotEvents v2 often puts number in 'name' or 'team_name' depending on endpoint, usually 'team.name' is number like '3150N'
        name: item.team.team_name || item.team.name, // Fallback
        organization: item.team.organization,
        grade: item.team.grade,
        region: item.team.region,
        country: item.team.country,
        skills: {
            rank: item.rank,
            combined_score: item.score,
            driver_score: item.driver_score,
            programming_score: item.programming_score
        }
    }));
}

export async function getTopRegions(): Promise<string[]> {
    const teams = await getSkillsStandings();
    const regionCounts: Record<string, number> = {};

    teams.forEach(team => {
        const region = team.region || team.country;
        if (region) {
            regionCounts[region] = (regionCounts[region] || 0) + 1;
        }
    });

    // Sort regions by count descending (competitiveness)
    return Object.keys(regionCounts).sort((a, b) => regionCounts[b] - regionCounts[a]);
}
