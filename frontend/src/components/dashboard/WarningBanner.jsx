import { cn } from "@/lib/utils";
import { AlertTriangle, XOctagon, Info, AlertCircle } from "lucide-react";

const levelConfig = {
  CRITICAL: {
    icon: XOctagon,
    bg: "bg-destructive/10",
    border: "border-destructive/30",
    text: "text-destructive",
    iconColor: "text-destructive"
  },
  HIGH: {
    icon: AlertTriangle,
    bg: "bg-accent/10",
    border: "border-accent/30",
    text: "text-accent",
    iconColor: "text-accent"
  },
  MEDIUM: {
    icon: AlertCircle,
    bg: "bg-secondary/10",
    border: "border-secondary/30",
    text: "text-secondary",
    iconColor: "text-secondary"
  },
  LOW: {
    icon: Info,
    bg: "bg-muted",
    border: "border-border",
    text: "text-muted-foreground",
    iconColor: "text-muted-foreground"
  }
};

export const WarningBanner = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="space-y-3" data-testid="warnings-container">
      {warnings.map((warning, idx) => {
        const config = levelConfig[warning.level] || levelConfig.LOW;
        const Icon = config.icon;

        return (
          <div 
            key={idx}
            className={cn(
              "p-4 rounded-lg border flex items-start gap-3",
              config.bg,
              config.border,
              warning.level === "CRITICAL" && "warning-pulse"
            )}
            data-testid={`warning-${warning.level.toLowerCase()}`}
          >
            <Icon className={cn("w-5 h-5 flex-shrink-0 mt-0.5", config.iconColor)} />
            <div className="flex-1">
              <p className={cn("text-sm font-medium", config.text)}>
                {warning.message}
              </p>
              {warning.action && (
                <p className="text-xs text-muted-foreground mt-1">
                  Action: {warning.action.replace(/_/g, ' ')}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default WarningBanner;
