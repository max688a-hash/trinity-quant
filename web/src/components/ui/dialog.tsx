import * as DialogPrimitive from "@radix-ui/react-dialog";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

const closers = new Set<() => void>();
export function bindModalCloser(fn: () => void): () => void {
  closers.add(fn);
  return () => {
    closers.delete(fn);
  };
}
export function closeModal(): void {
  for (const fn of closers) {
    fn();
  }
}

export function DialogContent({
  className,
  children,
  title,
}: {
  className?: string;
  children: ReactNode;
  title: string;
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-background/80" />
      <DialogPrimitive.Content
        onPointerDownOutside={() => closeModal()}
        className={cn(
          "fixed left-1/2 top-1/2 z-50 w-[min(92vw,480px)] -translate-x-1/2 -translate-y-1/2 rounded-[16px] border border-border bg-card p-4",
          className,
        )}
      >
        <DialogPrimitive.Title className="text-[18px] font-semibold">{title}</DialogPrimitive.Title>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
