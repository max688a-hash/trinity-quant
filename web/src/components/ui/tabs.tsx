import * as TabsPrimitive from "@radix-ui/react-tabs";
import type { ComponentPropsWithoutRef } from "react";
import { cn } from "../../lib/utils";

export const Tabs = TabsPrimitive.Root;
export const TabsList = ({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof TabsPrimitive.List>) => (
  <TabsPrimitive.List
    className={cn("flex gap-1 rounded-[12px] border border-border bg-background p-2", className)}
    {...props}
  />
);
export const TabsTrigger = ({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>) => (
  <TabsPrimitive.Trigger
    className={cn(
      "min-h-11 rounded-[8px] px-3 text-[13px] font-medium text-muted-foreground data-[state=active]:bg-card data-[state=active]:font-semibold data-[state=active]:text-primary",
      className,
    )}
    {...props}
  />
);
export const TabsContent = TabsPrimitive.Content;
