import { getEvents, getTopRegions } from "@/lib/api";
import EventsClient from "./EventsClient";

export const metadata = {
    title: "Events | V5 Hub",
    description: "Browse upcoming and past VEX V5 robotics competitions.",
};

export default async function EventsPage() {
    const events = await getEvents();
    const topRegions = await getTopRegions();

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-black tracking-tight">Competitions</h1>
            </div>

            <EventsClient initialEvents={events} topRegions={topRegions} />
        </div>
    );
}
