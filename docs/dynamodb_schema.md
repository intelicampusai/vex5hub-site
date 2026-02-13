# DynamoDB Schema Design (Single Table)

This document outlines the DynamoDB schema for the VEX V5 Hub project, optimized for "VEX V5 Hub" access patterns.

## Table Name: `vex5hub-data`

## Entities

### 1. Team Metadata
- **PK:** `TEAM#<TeamNumber>` (e.g., `TEAM#3150N`)
- **SK:** `METADATA`
- **Attributes:**
  - `name`: string
  - `organization`: string
  - `region`: string
  - `country`: string
  - `grade`: string
  - `stats`: map (wins, losses, ties, rank)
  - `skills`: map (score, rank)

### 2. Team Match Record (for History)
- **PK:** `TEAM#<TeamNumber>`
- **SK:** `MATCH#<Timestamp>#<MatchID>`
- **Attributes:**
  - `event_name`: string
  - `result`: string (WIN|LOSS|TIE)
  - `score_my`: number
  - `score_opp`: number
  - `video_url`: string (if exists)

### 3. Event
- **PK:** `SEASON#<SeasonID>` (e.g., `SEASON#190`)
- **SK:** `EVENT#<StartDate>#<SKU>`
- **Attributes:**
  - `name`: string
  - `venue`: string
  - `city`: string
  - `status`: string (active|future|past)
  - `livestream_url`: string

### 4. Global Ranking / Team List
- **GSI1-PK:** `SEASON#<SeasonID>`
- **GSI1-SK:** `RANK#<PaddedRank>#TEAM#<TeamNumber>`
- **Purpose:** Efficiently list teams by rank within a season.

## Access Patterns

| Pattern | PK | SK | Filter/GSI |
|---------|----|----|------------|
| Get Team metadata | `TEAM#3150N` | `METADATA` | |
| Get Team Match History | `TEAM#3150N` | `SK begins_with(MATCH#)` | Scan index backwards for recent |
| List Rankings | `SEASON#190` | `SK begins_with(RANK#)` | Using GSI1 |
| List Upcoming Events | `SEASON#190` | `SK begins_with(EVENT#)` | Sort by SK (Date) |
| Find Match Video | `MATCH#<MatchID>` | `METADATA` | (Optional separate table or PK) |

## Implementation Plan
1. Update Infrastructure (Terraform) to include the GSI.
2. Implement Python Lambda logic to fetch from RobotEvents and populate this table.
3. Integrate Next.js API/Direct DynamoDB access to consume this data.
