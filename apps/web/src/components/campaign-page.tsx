"use client";

import Image from "next/image";
import { Activity, ArrowRight, CalendarDays, HeartHandshake, ShieldCheck, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { DonationPanel } from "@/components/donation-panel";
import { CampaignSnapshot, fallbackSnapshot, fetchCampaignSnapshot } from "@/lib/api";

const statFormatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 1
});

const moneyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0
});

export function CampaignPage() {
  const [snapshot, setSnapshot] = useState<CampaignSnapshot>(fallbackSnapshot);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function refresh() {
      const data = await fetchCampaignSnapshot();
      if (mounted) {
        setSnapshot(data);
        setLoading(false);
      }
    }

    refresh();
    const interval = window.setInterval(refresh, 30_000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const started = useMemo(() => new Date(snapshot.campaign.startsAt), [snapshot.campaign.startsAt]);
  const ends = useMemo(() => new Date(snapshot.campaign.endsAt), [snapshot.campaign.endsAt]);

  return (
    <main className="min-h-screen bg-background">
      <section className="relative min-h-[680px] overflow-hidden text-white">
        <Image
          src="https://images.unsplash.com/photo-1469395446868-fb6a048d5ca3?auto=format&fit=crop&w=2200&q=85"
          alt="Runners moving together on an outdoor road"
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
        <div className="hero-mask absolute inset-0" />
        <div className="relative mx-auto flex min-h-[680px] w-full max-w-7xl flex-col px-5 py-6 sm:px-8 lg:px-10">
          <header className="flex items-center justify-between">
            <a href="#" className="flex items-center gap-3 text-sm font-semibold">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-white text-emerald-900">
                AE
              </span>
              <span>{snapshot.campaign.name}</span>
            </a>
            <nav className="hidden items-center gap-6 text-sm text-white/82 md:flex">
              <a href="#mission" className="hover:text-white">
                Mission
              </a>
              <a href="#runners" className="hover:text-white">
                Runners
              </a>
              <a href="#donations" className="hover:text-white">
                Donors
              </a>
              <a href="/admin" className="hover:text-white">
                Admin
              </a>
            </nav>
          </header>

          <div className="grid flex-1 items-end gap-10 py-14 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="max-w-3xl">
              <Badge variant="accent" className="mb-5 border-white/10 bg-white/88">
                {loading ? "Syncing live totals" : "Live campaign"}
              </Badge>
              <h1 className="text-5xl font-semibold leading-[0.98] tracking-normal sm:text-6xl lg:text-7xl">
                Every donation adds miles.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-white/86 sm:text-xl">
                {snapshot.campaign.mission}
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a href="#donate">
                  <Button size="lg" className="w-full bg-white text-emerald-950 hover:bg-white/90 sm:w-auto">
                    Donate now
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </a>
                <a href="#progress">
                  <Button
                    size="lg"
                    variant="outline"
                    className="w-full border-white/35 bg-white/10 text-white hover:bg-white/18 sm:w-auto"
                  >
                    See progress
                  </Button>
                </a>
              </div>
            </div>

            <Card className="border-white/18 bg-white/92 text-foreground shadow-2xl">
              <CardHeader>
                <CardDescription>Remaining miles</CardDescription>
                <CardTitle className="text-5xl">
                  {statFormatter.format(snapshot.totals.milesRemaining)}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <Progress value={snapshot.totals.completionPercent} />
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <Metric label="Raised" value={moneyFormatter.format(snapshot.totals.dollarsRaised)} />
                  <Metric label="Pledged" value={`${statFormatter.format(snapshot.totals.milesPledged)} mi`} />
                  <Metric label="Logged" value={`${statFormatter.format(snapshot.totals.milesCompleted)} mi`} />
                </div>
                <Separator />
                <div className="flex items-start gap-3 text-sm text-muted-foreground">
                  <CalendarDays className="mt-0.5 h-4 w-4 text-primary" />
                  <p>
                    Running from {started.toLocaleDateString()} through {ends.toLocaleDateString()}.
                    Every ${snapshot.campaign.dollarsPerMile} donated adds one mile.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section id="progress" className="border-b bg-card">
        <div className="mx-auto grid max-w-7xl gap-4 px-5 py-8 sm:grid-cols-2 sm:px-8 lg:grid-cols-4 lg:px-10">
          <StatCard label="Dollars raised" value={moneyFormatter.format(snapshot.totals.dollarsRaised)} />
          <StatCard label="Miles pledged" value={`${statFormatter.format(snapshot.totals.milesPledged)} mi`} />
          <StatCard label="Miles completed" value={`${statFormatter.format(snapshot.totals.milesCompleted)} mi`} />
          <StatCard label="Next milestone" value={`${snapshot.totals.nextMilestoneMiles} mi`} />
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-10 px-5 py-16 sm:px-8 lg:grid-cols-[0.85fr_1.15fr] lg:px-10">
        <div id="mission" className="space-y-5">
          <Badge variant="secondary">Mission</Badge>
          <h2 className="text-4xl font-semibold tracking-normal">
            A simple pledge mechanic that makes generosity visible.
          </h2>
          <p className="text-lg leading-8 text-muted-foreground">
            Donors support {snapshot.campaign.beneficiary}; brothers convert that support into
            accountable miles. The public site tracks aggregate progress while preserving athlete
            privacy.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <HeartHandshake className="h-6 w-6 text-primary" />
              <CardTitle className="text-xl">Donate</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">
              PayPal Checkout can surface Venmo for eligible US donors and sends verified webhooks
              back to the API.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Activity className="h-6 w-6 text-primary" />
              <CardTitle className="text-xl">Run</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">
              Brothers connect Strava once. Only eligible campaign miles count toward the aggregate.
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <ShieldCheck className="h-6 w-6 text-primary" />
              <CardTitle className="text-xl">Verify</CardTitle>
            </CardHeader>
            <CardContent className="text-sm leading-6 text-muted-foreground">
              Webhooks are idempotent, admin edits are audited, and public pages avoid individual
              Strava activity disclosure.
            </CardContent>
          </Card>
        </div>
      </section>

      <section id="donate" className="bg-muted">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 sm:px-8 lg:grid-cols-[1fr_0.92fr] lg:px-10">
          <div>
            <Badge variant="accent">Donation counter</Badge>
            <h2 className="mt-4 text-4xl font-semibold tracking-normal">Add the next mile.</h2>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-muted-foreground">
              Choose a donation amount and PayPal will handle payment details. When PayPal confirms
              the capture by webhook, the mile counter updates automatically.
            </p>
            <div className="mt-8 rounded-lg border bg-background p-5">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5 text-primary" />
                <p className="text-sm font-medium">
                  ${snapshot.campaign.dollarsPerMile} = 1 mile. A $50 donation adds 5 miles.
                </p>
              </div>
            </div>
          </div>
          <DonationPanel />
        </div>
      </section>

      <section id="runners" className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:px-10">
        <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <Badge variant="secondary">Brothers running</Badge>
            <h2 className="mt-4 text-4xl font-semibold tracking-normal">The roster</h2>
          </div>
          <p className="max-w-xl text-sm leading-6 text-muted-foreground">
            Public cards are curated profile content, not individual Strava activity feeds.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {snapshot.participants.map((participant) => (
            <Card key={participant.id}>
              <CardHeader className="flex-row items-center gap-4">
                <Avatar className="h-12 w-12">
                  {participant.avatarUrl ? (
                    <AvatarImage src={participant.avatarUrl} alt={participant.name} />
                  ) : null}
                  <AvatarFallback>{participant.initials}</AvatarFallback>
                </Avatar>
                <div>
                  <CardTitle className="text-lg">{participant.name}</CardTitle>
                  <CardDescription>{participant.role}</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="text-sm leading-6 text-muted-foreground">
                {participant.bio}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="donations" className="border-t bg-card">
        <div className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:px-10">
          <div className="mb-8">
            <Badge variant="secondary">Donation wall</Badge>
            <h2 className="mt-4 text-4xl font-semibold tracking-normal">Recent support</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {snapshot.donations.map((donation) => (
              <Card key={donation.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <CardTitle className="text-lg">{donation.donorName}</CardTitle>
                      <CardDescription>
                        {new Date(donation.createdAt).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <Badge variant="outline">{moneyFormatter.format(donation.amount)}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm leading-6 text-muted-foreground">
                  {donation.message}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted p-3">
      <div className="font-mono text-base font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-background p-5">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="mt-2 font-mono text-3xl font-semibold">{value}</div>
    </div>
  );
}

