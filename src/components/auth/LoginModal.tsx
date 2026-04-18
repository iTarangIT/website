"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, Store, Shield, LogIn } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { setRole, DEMO_CREDS, ROLE_HOME, type PortalRole } from "@/lib/session";

interface LoginModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ROLES: { id: PortalRole; icon: typeof BarChart3; title: string; subtitle: string }[] = [
  {
    id: "nbfc",
    icon: BarChart3,
    title: "NBFC",
    subtitle: "Portfolio, risk & collections",
  },
  {
    id: "dealer",
    icon: Store,
    title: "Dealer",
    subtitle: "Inventory, EMIs & service",
  },
  {
    id: "itarang",
    icon: Shield,
    title: "iTarang",
    subtitle: "Control tower & leads",
  },
];

export default function LoginModal({ open, onOpenChange }: LoginModalProps) {
  const router = useRouter();
  const [activeRole, setActiveRole] = useState<PortalRole>("nbfc");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = (role: PortalRole) => {
    setRole(role);
    onOpenChange(false);
    router.push(ROLE_HOME[role]);
  };

  const fillDemo = (role: PortalRole) => {
    const creds = DEMO_CREDS[role];
    setEmail(creds.email);
    setPassword(creds.password);
  };

  const onTabChange = (v: string) => {
    setActiveRole(v as PortalRole);
    setEmail("");
    setPassword("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[440px] bg-white">
        <DialogHeader>
          <DialogTitle className="text-xl text-gray-900">Log in to iTarang</DialogTitle>
          <DialogDescription className="text-gray-500">
            Pick a role to explore the demo portal. All credentials are hardcoded.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeRole} onValueChange={onTabChange} className="w-full">
          <TabsList className="grid grid-cols-3 w-full h-auto bg-gray-100">
            {ROLES.map((r) => (
              <TabsTrigger key={r.id} value={r.id} className="flex flex-col gap-1 py-2.5">
                <r.icon className="h-4 w-4" />
                <span className="text-xs">{r.title}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {ROLES.map((r) => {
            const creds = DEMO_CREDS[r.id];
            return (
              <TabsContent key={r.id} value={r.id} className="mt-5 space-y-4">
                <div className="rounded-lg bg-brand-50 border border-brand-100 px-3 py-2.5 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-brand-700">
                      Demo: <span className="font-mono">{creds.email} / {creds.password}</span>
                    </p>
                    <p className="text-[11px] text-brand-500 mt-0.5">Opens the {creds.label} workspace.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => fillDemo(r.id)}
                    className="shrink-0 text-xs font-semibold text-brand-600 hover:text-brand-700 px-2 py-1 rounded-md hover:bg-brand-100 transition-colors"
                  >
                    Use demo
                  </button>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    submit(r.id);
                  }}
                  className="space-y-3"
                >
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1.5">Email</label>
                    <Input
                      type="text"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder={creds.email}
                      autoComplete="off"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1.5">Password</label>
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••"
                      autoComplete="off"
                    />
                  </div>
                  <Button type="submit" size="md" className="w-full justify-center">
                    <LogIn className="h-4 w-4 mr-2" />
                    Log in as {r.title}
                  </Button>
                </form>
              </TabsContent>
            );
          })}
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
