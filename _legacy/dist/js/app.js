/**
 * VEX V5 Hub — Multi-Page Application
 * Backend: API Gateway + Lambda + DynamoDB
 * Every data item links to its official source.
 */

const CONFIG = {
    // API base URL — set after Terraform deploy
    // Will be updated programmatically; falls back to relative /api path
    apiBaseUrl: '',
    animationDelay: 80
};

// ===================================
// Initialization
// ===================================
document.addEventListener('DOMContentLoaded', async () => {
    await detectApiUrl();
    initNavigation();
    initPage();
    initScrollAnimations();
});

async function detectApiUrl() {
    // Try reading API URL from a config endpoint, or fall back to the
    // API Gateway URL injected at deploy time.
    try {
        const res = await fetch('/data/config.json');
        if (res.ok) {
            const cfg = await res.json();
            if (cfg.apiBaseUrl) CONFIG.apiBaseUrl = cfg.apiBaseUrl;
        }
    } catch (_) { /* ignore — use default */ }
}

function initNavigation() {
    const toggle = document.getElementById('nav-toggle');
    const menu = document.querySelector('.nav__menu');
    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('nav__menu--open');
            toggle.classList.toggle('nav__toggle--active');
        });
    }
    document.querySelectorAll('.nav__link').forEach(link => {
        link.addEventListener('click', () => {
            menu?.classList.remove('nav__menu--open');
            toggle?.classList.remove('nav__toggle--active');
        });
    });
}

function initPage() {
    const path = location.pathname.split('/').pop() || 'index.html';
    if (path === 'competitions.html') {
        loadCompetitions();
        loadEvents();
    } else if (path === 'robots.html') {
        loadRobots();
    } else if (path === 'teams.html') {
        initTeamsPage();
    }
}

// ===================================
// API Client
// ===================================
async function apiGet(endpoint) {
    const url = CONFIG.apiBaseUrl
        ? `${CONFIG.apiBaseUrl}${endpoint}`
        : endpoint;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const text = await response.text();
        return JSON.parse(text);
    } catch (error) {
        console.warn(`API error ${endpoint}:`, error.message);
        return null;
    }
}

// ===================================
// Source Link Helper
// ===================================
function sourceLink(url, label) {
    if (!url) return '';
    return `<a href="${esc(url)}" target="_blank" rel="noopener" class="source-link" title="View on official source">
        <span class="source-link__icon">🔗</span>
        <span class="source-link__label">${esc(label || 'Official Source')}</span>
    </a>`;
}

// ===================================
// Competitions Page
// ===================================
async function loadCompetitions() {
    const data = await apiGet('/api/competitions');
    const container = document.getElementById('competition-cards');
    if (!data || !container) return;
    container.innerHTML = '';
    const competitions = Array.isArray(data) ? data : (data.competitions || []);
    if (competitions.length > 0) {
        competitions.forEach((comp, i) => container.appendChild(createCompetitionCard(comp, i)));
    } else {
        container.innerHTML = emptyState('No competition data available yet', 'Check back soon!');
    }
}

function createCompetitionCard(comp, index) {
    const container = document.getElementById('competitions-grid');
    if (!container) return;

    if (!data || data.length === 0) {
        container.innerHTML = emptyState('No competitions data', 'Check back later.');
        return;
    }

    // Render Table
    let html = `
        <div class="table-container">
            <table class="teams-table">
                <thead>
                    <tr>
                        <th style="width: 140px;">Date</th>
                        <th>Event</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th class="th-expand"></th>
                    </tr>
                </thead>
                <tbody>
    `;

    data.forEach(comp => {
        const icon = comp.icon || '📅';
        const statusClass = comp.status === 'live' ? 'status-live' : comp.status === 'active' ? 'status-active' : 'status-past';

        html += `
            <tr class="team-row comp-row">
                <td class="td-date">${esc(comp.date)}</td>
                <td class="td-name">
                    <div class="comp-name-cell">
                        <span class="comp-icon">${icon}</span>
                        <span>${esc(comp.title)}</span>
                    </div>
                </td>
                <td class="td-location">${esc(comp.location)}</td>
                <td class="td-status"><span class="badge-status ${statusClass}">${esc(comp.status)}</span></td>
                <td class="td-expand">▼</td>
            </tr>
            <tr class="team-details-row">
                <td colspan="5">
                     <div class="team-details-content">
                        <p class="comp-desc">${esc(comp.description)}</p>
                        <div class="comp-meta">
                            <span>👥 ${esc(comp.participants)}</span>
                            ${comp.source_url ? `<a href="${comp.source_url}" target="_blank" class="robot-events-link">View Details ↗</a>` : ''}
                        </div>
                     </div>
                </td>
            </tr>
         `;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;

    // Add interactions
    addTableInteractions(container);
}

function addTableInteractions(container) {
    container.querySelectorAll('.team-row').forEach(row => {
        row.addEventListener('click', () => {
            row.classList.toggle('team-row--expanded');
            row.nextElementSibling.classList.toggle('team-details-row--visible');
        });
    });
}

// Stub for events if called separately
async function loadEvents() {
    // Events loading can be added here if needed, or merged into competitions
}

// ===================================
// Robots Page
// ===================================
async function loadRobots() {
    const data = await apiGet('/api/robots');
    const container = document.getElementById('robots-grid');
    const techGrid = document.getElementById('tech-grid');

    if (!data) return;
    const robots = Array.isArray(data) ? data : (data.viral || []);

    if (container) {
        if (robots.length === 0) {
            container.innerHTML = emptyState('No robot designs yet', 'Coming soon!');
        } else {
            // Render Robots Table
            let html = `
                <div class="table-container">
                    <table class="teams-table">
                        <thead>
                            <tr>
                                <th>Robot</th>
                                <th>Team</th>
                                <th>Description</th>
                                <th class="th-expand"></th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            robots.forEach(robot => {
                const icon = robot.icon || '🤖';
                const title = robot.title || robot.name || 'Robot';

                html += `
                    <tr class="team-row">
                        <td class="td-name">
                            <div class="comp-name-cell">
                                <span class="comp-icon">${icon}</span>
                                <span>${esc(title)}</span>
                            </div>
                        </td>
                        <td class="td-team">${esc(robot.team || 'Unknown')}</td>
                        <td class="td-desc-short">${esc(robot.description || '').substring(0, 60)}...</td>
                        <td class="td-expand">▼</td>
                    </tr>
                    <tr class="team-details-row">
                        <td colspan="4">
                             <div class="team-details-content">
                                <p>${esc(robot.description)}</p>
                                <div class="video-actions">
                                    ${robot.url ? `<a href="${robot.url}" target="_blank" class="action-btn">📺 Watch Video</a>` : ''}
                                    ${robot.source_url ? `<a href="${robot.source_url}" target="_blank" class="robot-events-link">View Team ↗</a>` : ''}
                                </div>
                             </div>
                        </td>
                    </tr>
                 `;
            });

            html += `</tbody></table></div>`;
            container.innerHTML = html;
            addTableInteractions(container);
        }
    }

    if (techGrid) {
        techGrid.innerHTML = '';
        const breakdowns = data.techBreakdowns || [];
        breakdowns.forEach((tech, i) => techGrid.appendChild(createTechCard(tech, i)));
    }
}

function createTechCard(tech, index) {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.animationDelay = `${index * CONFIG.animationDelay}ms`;
    card.innerHTML = `
        <div class="card__header">
            <span class="card__icon">🔧</span>
            <h4 class="card__title">${esc(tech.title)}</h4>
        </div>
        <p class="card__description">${esc(tech.description)}</p>
        ${tech.source_url ? `<div class="card__source">${sourceLink(tech.source_url, 'VEX Forum')}</div>` : ''}
    `;
    if (tech.source_url) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.source-link')) window.open(tech.source_url, '_blank');
        });
    }
    return card;
}

// ===================================
// Teams Page
// ===================================
let teamsData = null;

async function initTeamsPage() {
    let data = await apiGet('/api/teams');

    if (!data || !data.regions) {
        const grid = document.getElementById('teams-grid');
        if (grid) grid.innerHTML = emptyState('Unable to load teams data', 'Please try again later.');
        return;
    }
    teamsData = data.regions;
    renderFilterBar();
    // Default to Ontario, fall back to first region if not found
    if (teamsData.some(r => r.id === 'ontario')) {
        selectRegion('ontario');
    } else {
        selectRegion(teamsData[0].id);
    }
}

function renderFilterBar() {
    const bar = document.getElementById('region-filter');
    if (!bar) return;
    bar.innerHTML = '';
    teamsData.forEach(region => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.textContent = region.name;
        btn.dataset.region = region.id;
        btn.addEventListener('click', () => selectRegion(region.id));
        bar.appendChild(btn);
    });
}

function selectRegion(regionId) {
    const region = teamsData.find(r => r.id === regionId);
    if (!region) return;

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('filter-btn--active', btn.dataset.region === regionId);
    });

    const heading = document.getElementById('region-heading');
    if (heading) {
        heading.innerHTML = `
            <h3 class="region-heading__title">Top Teams in ${esc(region.name)}</h3>
            <p class="region-heading__country">${esc(region.country)}</p>
        `;
    }

    const grid = document.getElementById('teams-grid');
    if (!grid) return;
    grid.innerHTML = `
        <div class="table-container">
            <table class="teams-table">
                <thead>
                    <tr>
                        <th class="th-rank">Rank</th>
                        <th class="th-number">Team</th>
                        <th class="th-name">Name</th>
                        <th class="th-grade">Grade</th>
                        <th class="th-skills">Skills</th>
                        <th class="th-record">Record</th>
                        <th class="th-qualified">Qualified</th>
                        <th class="th-expand"></th>
                    </tr>
                </thead>
                <tbody id="teams-table-body"></tbody>
            </table>
        </div>
    `;

    const tbody = document.getElementById('teams-table-body');
    region.teams.sort((a, b) => a.rank - b.rank).forEach((team, i) => {
        tbody.appendChild(createTeamRow(team, i));
    });
}

function createTeamRow(team, index) {
    const fragment = document.createDocumentFragment();

    // Main Row
    const row = document.createElement('tr');
    row.className = 'team-row';
    if (index < 3) row.classList.add(`team-row--top-${index + 1}`);

    const grade = team.division === 'Middle School' ? 'MS' : 'HS';
    const qualified = team.worlds_qualified ? '<span class="badge-qualified">Worlds</span>' : '';
    const winRate = team.wins + team.losses > 0
        ? Math.round((team.wins / (team.wins + team.losses)) * 100) + '%'
        : '-';

    // Rank Change Calculation
    let changeHtml = '<span class="rank-change rank-change--same">-</span>';
    if (team.rank_change > 0) {
        changeHtml = `<span class="rank-change rank-change--up">▲ ${team.rank_change}</span>`;
    } else if (team.rank_change < 0) {
        changeHtml = `<span class="rank-change rank-change--down">▼ ${Math.abs(team.rank_change)}</span>`;
    }

    row.innerHTML = `
        <td class="td-rank">
            <span class="rank-badge">${team.rank}</span>
            ${changeHtml}
        </td>
        <td class="td-number">${esc(team.number)}</td>
        <td class="td-name">${esc(team.name)}</td>
        <td class="td-grade"><span class="badge-grade ${grade.toLowerCase()}">${grade}</span></td>
        <td class="td-skills">${team.skills_score}</td>
        <td class="td-record">${team.wins}W - ${team.losses}L <span class="win-rate">(${winRate})</span></td>
        <td class="td-qualified">${qualified}</td>
        <td class="td-expand">▼</td>
    `;

    // Details Row
    const detailsRow = document.createElement('tr');
    detailsRow.className = 'team-details-row';

    const awardBadges = (team.awards || []).map(a => `<span class="award-badge">🏅 ${esc(a)}</span>`).join('');
    const matchVideosHtml = buildMatchVideosHtml(team); // Reuse existing video builder

    detailsRow.innerHTML = `
        <td colspan="8">
            <div class="team-details-content">
                <div class="details-grid">
                    <div class="details-section">
                        <h4>Awards</h4>
                        <div class="awards-list">${awardBadges || '<span class="text-muted">No awards recorded</span>'}</div>
                    </div>
                    <div class="details-section">
                        <h4>Stats</h4>
                        <div class="stats-list">
                            <span>World Skills Rank: <strong>#${team.skills_rank}</strong></span>
                            <span>Win Rate: <strong>${winRate}</strong></span>
                        </div>
                         <a href="${esc(team.source_url || `https://www.robotevents.com/teams/VRC/${team.number}`)}" 
                           target="_blank" rel="noopener" class="robot-events-link">
                            View on RobotEvents ↗
                        </a>
                    </div>
                </div>
                ${matchVideosHtml ? `<div class="videos-section">${matchVideosHtml}</div>` : ''}
            </div>
        </td>
    `;

    // Toggle Logic
    row.addEventListener('click', () => {
        row.classList.toggle('team-row--expanded');
        detailsRow.classList.toggle('team-details-row--visible');
    });

    // Re-attach toggle listeners for match video accordions
    if (team.match_videos && team.match_videos.length > 0) {
        setTimeout(() => {
            detailsRow.querySelectorAll('.team-card__videos-toggle').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const content = btn.nextElementSibling;
                    const isOpen = btn.classList.toggle('team-card__videos-toggle--open');
                    content.style.maxHeight = isOpen ? content.scrollHeight + 'px' : '0';
                });
            });
        }, 0);
    }

    fragment.appendChild(row);
    fragment.appendChild(detailsRow);
    return fragment;
}

function buildMatchVideosHtml(team) {
    if (!team.match_videos || team.match_videos.length === 0) return '';

    let html = '<div class="team-card__videos">';

    team.match_videos.forEach(event => {
        // Group matches by type
        const quals = event.matches.filter(m => m.match.startsWith('Q'));
        const elims = event.matches.filter(m => !m.match.startsWith('Q'));

        html += `
            <button class="team-card__videos-toggle" type="button">
                <span class="team-card__videos-toggle-icon">📹</span>
                <span class="team-card__videos-toggle-text">Match Videos — ${esc(event.event)}</span>
                <span class="team-card__videos-toggle-date">${esc(event.event_date)}</span>
                <span class="team-card__videos-toggle-arrow">▼</span>
            </button>
            <div class="team-card__videos-content">
                <div class="team-card__event-header">
                    <a href="${esc(event.event_url)}" target="_blank" rel="noopener" class="team-card__event-link">
                        View on RobotEvents ↗
                    </a>
                </div>
        `;

        if (quals.length > 0) {
            html += `<div class="team-card__match-group">
                <span class="team-card__match-group-label">Qualification Matches</span>
                <div class="team-card__match-list">`;
            quals.forEach(m => {
                html += createMatchLinkHtml(m);
            });
            html += `</div></div>`;
        }

        if (elims.length > 0) {
            html += `<div class="team-card__match-group">
                <span class="team-card__match-group-label">Elimination Matches</span>
                <div class="team-card__match-list">`;
            elims.forEach(m => {
                html += createMatchLinkHtml(m);
            });
            html += `</div></div>`;
        }

        html += `</div>`;
    });

    html += '</div>';
    return html;
}

function createMatchLinkHtml(match) {
    const resultClass = match.result === 'W' ? 'team-card__match-link--win' : 'team-card__match-link--loss';
    const resultIcon = match.result === 'W' ? '✅' : '❌';
    const matchLabel = formatMatchName(match.match);

    return `
        <a href="${esc(match.video_url)}" target="_blank" rel="noopener" 
           class="team-card__match-link ${resultClass}"
           title="Watch ${matchLabel} (${match.score})">
            <span class="team-card__match-name">${esc(matchLabel)}</span>
            <span class="team-card__match-score">${esc(match.score)}</span>
            <span class="team-card__match-result">${resultIcon}</span>
            <span class="team-card__match-play">▶</span>
        </a>
    `;
}

function formatMatchName(matchId) {
    if (matchId.startsWith('QF')) return `Quarterfinal #${matchId.split('-')[1]}`;
    if (matchId.startsWith('Q')) return `Qual ${matchId.slice(1)}`;
    if (matchId.startsWith('R16')) return `Round of 16 #${matchId.split('-')[1]}`;
    if (matchId.startsWith('SF')) return `Semifinal #${matchId.split('-')[1]}`;
    if (matchId.startsWith('F')) return `Final #${matchId.split('-')[1]}`;
    return matchId;
}

// ===================================
// Scroll Animations
// ===================================
function initScrollAnimations() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('animate-in');
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.card, .home-card, .team-card, .timeline__item, .section__header').forEach(el => {
        observer.observe(el);
    });
}

// ===================================
// Utilities
// ===================================
function esc(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function emptyState(title, subtitle) {
    return `<div class="empty-state"><p class="empty-state__title">${esc(title)}</p><p class="empty-state__subtitle">${esc(subtitle)}</p></div>`;
}
