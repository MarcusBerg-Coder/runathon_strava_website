"use client";

import { Loader2, LogIn, PlusCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { CampaignSnapshot, fallbackSnapshot, fetchCampaignSnapshot, getApiBase } from "@/lib/api";

export function AdminDashboard() {
  const [snapshot, setSnapshot] = useState<CampaignSnapshot>(fallbackSnapshot);
  const [password, setPassword] = useState("");
  const [reason, setReason] = useState("");
  const [dollars, setDollars] = useState(0);
  const [miles, setMiles] = useState(0);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setSnapshot(await fetchCampaignSnapshot());
  }

  useEffect(() => {
    let mounted = true;

    fetchCampaignSnapshot().then((data) => {
      if (mounted) {
        setSnapshot(data);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus(null);

    try {
      const response = await fetch(`${getApiBase()}/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ password })
      });

      if (!response.ok) {
        throw new Error("Admin login failed");
      }

      setPassword("");
      setStatus("Admin session active.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Admin login failed");
    } finally {
      setBusy(false);
    }
  }

  async function submitAdjustment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus(null);

    try {
      const response = await fetch(`${getApiBase()}/admin/manual-adjustments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          dollars_delta: dollars,
          miles_delta: miles,
          reason
        })
      });

      if (!response.ok) {
        throw new Error("Adjustment failed. Log in first and include an audit reason.");
      }

      setDollars(0);
      setMiles(0);
      setReason("");
      setStatus("Adjustment recorded.");
      await refresh();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Adjustment failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-muted">
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:px-10">
        <header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <Badge variant="secondary">Admin</Badge>
            <h1 className="mt-3 text-4xl font-semibold tracking-normal">Runathon control room</h1>
          </div>
          <Button variant="outline" onClick={refresh}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </header>

        <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  Sign in
                </CardTitle>
                <CardDescription>Creates a signed HttpOnly admin session cookie.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={login} className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="password">Admin password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                    />
                  </div>
                  <Button type="submit" disabled={busy}>
                    {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
                    Sign in
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Manual adjustment</CardTitle>
                <CardDescription>Use only for reconciliation or approved corrections.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={submitAdjustment} className="space-y-4">
                  <div className="grid gap-2">
                    <Label htmlFor="dollars">Dollars delta</Label>
                    <Input
                      id="dollars"
                      type="number"
                      value={dollars}
                      onChange={(event) => setDollars(Number(event.target.value))}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="miles">Miles delta</Label>
                    <Input
                      id="miles"
                      type="number"
                      step="0.1"
                      value={miles}
                      onChange={(event) => setMiles(Number(event.target.value))}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="reason">Audit reason</Label>
                    <Input
                      id="reason"
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                    />
                  </div>
                  <Button type="submit" disabled={busy}>
                    <PlusCircle className="h-4 w-4" />
                    Record adjustment
                  </Button>
                </form>
              </CardContent>
            </Card>

            {status ? <p className="text-sm text-muted-foreground">{status}</p> : null}
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Campaign totals</CardTitle>
                <CardDescription>Verified donations plus included activities.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <Progress value={snapshot.totals.completionPercent} />
                <div className="grid gap-3 sm:grid-cols-4">
                  <AdminMetric label="Raised" value={`$${snapshot.totals.dollarsRaised}`} />
                  <AdminMetric label="Pledged" value={`${snapshot.totals.milesPledged} mi`} />
                  <AdminMetric label="Completed" value={`${snapshot.totals.milesCompleted} mi`} />
                  <AdminMetric label="Remaining" value={`${snapshot.totals.milesRemaining} mi`} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Donation wall</CardTitle>
                <CardDescription>Recent public donor entries.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Donor</TableHead>
                      <TableHead>Message</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {snapshot.donations.map((donation) => (
                      <TableRow key={donation.id}>
                        <TableCell className="font-medium">{donation.donorName}</TableCell>
                        <TableCell>{donation.message}</TableCell>
                        <TableCell className="text-right">${donation.amount}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}

function AdminMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-background p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-2 font-mono text-xl font-semibold">{value}</div>
    </div>
  );
}
