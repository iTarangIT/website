"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button-shadcn";
import GatedForm from "@/components/shared/GatedForm";
import { FileText } from "lucide-react";

export default function DeckRequestDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          size="lg"
          className="w-full bg-white text-brand-700 hover:bg-brand-50 h-14 text-lg font-semibold rounded-2xl shadow-lg shadow-white/10 border border-white/20 font-sans transition-all hover:shadow-xl"
        >
          <FileText className="h-5 w-5 mr-2" />
          Request Pitch Deck
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[480px] rounded-3xl border-gray-200/60">
        <DialogHeader>
          <DialogTitle className="text-xl">Request Pitch Deck</DialogTitle>
          <DialogDescription className="font-sans">
            Share your details and we&apos;ll send over the full deck.
          </DialogDescription>
        </DialogHeader>
        <GatedForm
          title=""
          description=""
        />
      </DialogContent>
    </Dialog>
  );
}
