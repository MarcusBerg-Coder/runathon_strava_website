export type CampaignSnapshot = {
  campaign: {
    name: string;
    slug: string;
    beneficiary: string;
    mission: string;
    dollarsPerMile: number;
    startsAt: string;
    endsAt: string;
  };
  totals: {
    dollarsRaised: number;
    milesPledged: number;
    milesCompleted: number;
    milesRemaining: number;
    completionPercent: number;
    nextMilestoneMiles: number;
  };
  participants: Array<{
    id: string;
    name: string;
    role: string;
    initials: string;
    bio: string;
    avatarUrl?: string | null;
  }>;
  donations: Array<{
    id: string;
    donorName: string;
    message: string;
    amount: number;
    createdAt: string;
  }>;
};

const fallbackSnapshot: CampaignSnapshot = {
  campaign: {
    name: "AEPI Runathon",
    slug: "aepi-runathon",
    beneficiary: "Chapter philanthropy partner",
    mission:
      "Brothers are turning every donation into miles for a cause our chapter is proud to support.",
    dollarsPerMile: 10,
    startsAt: "2026-05-01T00:00:00Z",
    endsAt: "2026-06-01T00:00:00Z"
  },
  totals: {
    dollarsRaised: 1840,
    milesPledged: 184,
    milesCompleted: 71.6,
    milesRemaining: 112.4,
    completionPercent: 38.9,
    nextMilestoneMiles: 200
  },
  participants: [
    {
      id: "1",
      name: "Noah Cohen",
      role: "Run captain",
      initials: "NC",
      bio: "Coordinates weekly group runs and keeps the board honest."
    },
    {
      id: "2",
      name: "Eli Rosen",
      role: "Distance lead",
      initials: "ER",
      bio: "Logs long efforts and recruits brothers for weekend mileage."
    },
    {
      id: "3",
      name: "Sam Levine",
      role: "Outreach",
      initials: "SL",
      bio: "Connects donors with the mission behind every mile."
    }
  ],
  donations: [
    {
      id: "sample-1",
      donorName: "Anonymous",
      message: "Run hard for a good cause.",
      amount: 100,
      createdAt: "2026-05-09T16:30:00Z"
    },
    {
      id: "sample-2",
      donorName: "The Goldberg Family",
      message: "Proud of the brothers.",
      amount: 180,
      createdAt: "2026-05-08T19:10:00Z"
    }
  ]
};

export function getApiBase() {
  return process.env.NEXT_PUBLIC_API_URL || "/api";
}

export async function fetchCampaignSnapshot(): Promise<CampaignSnapshot> {
  try {
    const response = await fetch(`${getApiBase()}/campaign/current`, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error(`Campaign request failed: ${response.status}`);
    }

    return (await response.json()) as CampaignSnapshot;
  } catch {
    return fallbackSnapshot;
  }
}

export { fallbackSnapshot };

