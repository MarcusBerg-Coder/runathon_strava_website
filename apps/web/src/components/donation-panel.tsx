"use client";

import { CreditCard, ExternalLink, Loader2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { getApiBase } from "@/lib/api";

type PayPalActions = {
  order: {
    capture: () => Promise<unknown>;
  };
};

type PayPalNamespace = {
  Buttons: (options: {
    style?: Record<string, string | number>;
    createOrder: () => Promise<string>;
    onApprove: (data: { orderID: string }, actions: PayPalActions) => Promise<void>;
    onError: (error: unknown) => void;
  }) => {
    render: (selector: string | HTMLElement) => Promise<void>;
  };
};

declare global {
  interface Window {
    paypal?: PayPalNamespace;
  }
}

const presetAmounts = [25, 50, 100, 180];

export function DonationPanel() {
  const [amount, setAmount] = useState(50);
  const [donorName, setDonorName] = useState("");
  const [message, setMessage] = useState("");
  const [anonymous, setAnonymous] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const buttonContainerRef = useRef<HTMLDivElement>(null);
  const paypalClientId = process.env.NEXT_PUBLIC_PAYPAL_CLIENT_ID;

  const miles = useMemo(() => amount / 10, [amount]);

  const createOrder = useCallback(async () => {
    const response = await fetch(`${getApiBase()}/paypal/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amount,
        donor_name: anonymous ? "" : donorName,
        message,
        anonymous
      })
    });

    if (!response.ok) {
      throw new Error("Unable to create PayPal order");
    }

    return (await response.json()) as { id: string; approve_url?: string };
  }, [amount, anonymous, donorName, message]);

  const captureOrder = useCallback(async (orderId: string) => {
    const response = await fetch(`${getApiBase()}/paypal/orders/${orderId}/capture`, {
      method: "POST"
    });

    if (!response.ok) {
      throw new Error("Unable to capture PayPal order");
    }
  }, []);

  async function openHostedCheckout() {
    setIsLoading(true);
    setStatus(null);

    try {
      const order = await createOrder();
      if (order.approve_url) {
        window.location.href = order.approve_url;
        return;
      }
      setStatus("Order created. Configure PayPal return URLs to finish hosted checkout.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Donation could not start.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (!paypalClientId || !buttonContainerRef.current) {
      return;
    }

    const scriptId = "paypal-js-sdk";
    const existing = document.getElementById(scriptId);

    function renderButtons() {
      if (!window.paypal || !buttonContainerRef.current) {
        return;
      }

      buttonContainerRef.current.innerHTML = "";
      window.paypal
        .Buttons({
          style: {
            layout: "vertical",
            shape: "rect",
            label: "donate"
          },
          createOrder: async () => {
            const order = await createOrder();
            return order.id;
          },
          onApprove: async (data) => {
            await captureOrder(data.orderID);
            setStatus("Payment approved. The public counter updates after PayPal sends the webhook.");
          },
          onError: (error) => {
            console.error(error);
            setStatus("PayPal could not complete this donation.");
          }
        })
        .render(buttonContainerRef.current);
    }

    if (existing) {
      renderButtons();
      return;
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = `https://www.paypal.com/sdk/js?client-id=${paypalClientId}&currency=USD&intent=capture&enable-funding=venmo`;
    script.async = true;
    script.onload = renderButtons;
    document.body.appendChild(script);
  }, [captureOrder, createOrder, paypalClientId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Donate</CardTitle>
        <CardDescription>PayPal Checkout shows Venmo where eligible.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid grid-cols-4 gap-2">
          {presetAmounts.map((preset) => (
            <Button
              key={preset}
              type="button"
              variant={amount === preset ? "default" : "outline"}
              onClick={() => setAmount(preset)}
            >
              ${preset}
            </Button>
          ))}
        </div>

        <div className="grid gap-2">
          <Label htmlFor="amount">Custom amount</Label>
          <Input
            id="amount"
            type="number"
            min={1}
            value={amount}
            onChange={(event) => setAmount(Number(event.target.value))}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="donor-name">Display name</Label>
          <Input
            id="donor-name"
            value={donorName}
            disabled={anonymous}
            placeholder="Anonymous by default"
            onChange={(event) => setDonorName(event.target.value)}
          />
        </div>

        <div className="grid gap-2">
          <Label htmlFor="message">Message</Label>
          <Input
            id="message"
            value={message}
            placeholder="Optional note for the donation wall"
            onChange={(event) => setMessage(event.target.value)}
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={anonymous}
            onChange={(event) => setAnonymous(event.target.checked)}
          />
          Keep my name anonymous
        </label>

        <div className="rounded-md bg-muted p-4 text-sm">
          This adds <span className="font-mono font-semibold">{miles.toFixed(1)}</span> pledged
          miles after PayPal confirms payment.
        </div>

        {paypalClientId ? <div ref={buttonContainerRef} className="min-h-12" /> : null}

        {!paypalClientId ? (
          <Button className="w-full" onClick={openHostedCheckout} disabled={isLoading}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <CreditCard className="h-4 w-4" />}
            Start PayPal donation
            <ExternalLink className="h-4 w-4" />
          </Button>
        ) : null}

        {status ? <p className="text-sm text-muted-foreground">{status}</p> : null}
      </CardContent>
    </Card>
  );
}
