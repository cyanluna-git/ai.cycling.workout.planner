import { useTranslation } from 'react-i18next';
import { useState, type ReactNode } from "react";
import {
  Zap, HardDrive, RefreshCw, CalendarDays, Settings, Sparkles,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  hasNewVersion,
  getLatestUpdate,
  markVersionAsSeen,
  type VersionUpdate,
} from "@/lib/version";

/** Resolve icon name string to a Lucide React icon element */
const FEATURE_ICON_MAP: Record<string, ReactNode> = {
  "zap": <Zap className="h-7 w-7" />,
  "hard-drive": <HardDrive className="h-7 w-7" />,
  "refresh-cw": <RefreshCw className="h-7 w-7" />,
  "calendar-days": <CalendarDays className="h-7 w-7" />,
  "settings": <Settings className="h-7 w-7" />,
};

function resolveFeatureIcon(iconName?: string): ReactNode {
  if (!iconName) return <Sparkles className="h-7 w-7" />;
  return FEATURE_ICON_MAP[iconName] ?? <Sparkles className="h-7 w-7" />;
}

/**
 * UpdateAnnouncementModal
 *
 * Displays update announcements to users when a new version is detected.
 * Uses localStorage to track which version the user has last seen.
 *
 * Features:
 * - Automatic detection of new versions on app load
 * - Beautiful modal UI with feature highlights
 * - Persistent tracking of seen versions
 * - Option to dismiss or view details
 */
export function UpdateAnnouncementModal() {
  const { t } = useTranslation();
  const initialUpdate = hasNewVersion() ? getLatestUpdate() : null;
  const [update] = useState<VersionUpdate | null>(initialUpdate);
  const [open, setOpen] = useState(initialUpdate !== null);

  const handleClose = () => {
    if (update) {
      markVersionAsSeen(update.version);
    }
    setOpen(false);
  };

  if (!update) return null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-lg px-3 py-1 text-sm font-bold">
              v{update.version}
            </div>
            <DialogTitle className="text-xl">{update.title}</DialogTitle>
          </div>
          <DialogDescription className="text-muted-foreground">
            {new Date(update.date).toLocaleDateString("ko-KR", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}{" "}
            {t("update.announcement")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 my-4">
          <div className="text-sm font-medium text-foreground">
            {t("update.newFeatures")}
          </div>

          {update.features.map((feature, index) => (
            <div
              key={index}
              className="flex gap-4 p-4 rounded-lg bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 border border-blue-100 dark:border-blue-900/30"
            >
              {feature.icon && (
                <div className="flex-shrink-0 leading-none text-primary">
                  {resolveFeatureIcon(feature.icon)}
                </div>
              )}
              <div className="flex-1 space-y-1">
                <div className="font-semibold text-foreground">
                  {feature.title}
                </div>
                <div className="text-sm text-muted-foreground">
                  {feature.description}
                </div>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleClose}
            className="flex-1 sm:flex-none"
          >
            {t("update.dismiss")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
