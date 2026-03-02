/**
 * Loading skeleton components for dashboard
 * Provides immediate visual feedback while data is loading
 */

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function FitnessCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-48 mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Training Metrics */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-3 w-12" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-3 w-12" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-3 w-12" />
            </div>
          </div>
        </div>

        {/* Form Status */}
        <Skeleton className="h-10 w-full" />
      </CardContent>
    </Card>
  );
}

export function WellnessCardSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-48 mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Readiness */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-24" />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-6 w-20" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function WeeklyCalendarSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Week Navigation */}
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-8 w-8" />
        </div>

        {/* Calendar Grid */}
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center space-x-3 p-3 border rounded">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function WeeklyPlanSkeleton() {
  return (
    <Card>
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-8 w-24" />
        </div>
        <Skeleton className="h-4 w-64" />
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Week Navigation */}
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-8" />
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-8 w-8" />
        </div>

        {/* Training Style & TSS */}
        <div className="flex items-center justify-between p-4 bg-muted rounded">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-5 w-24" />
        </div>

        {/* Daily Workouts */}
        <div className="space-y-2">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="p-4 border rounded space-y-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-4 w-full" />
              <div className="flex items-center justify-between">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function TodayWorkoutSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-4 w-64 mt-2" />
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Workout Info */}
        <div className="space-y-3">
          <Skeleton className="h-8 w-full" />
          <div className="flex items-center space-x-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-24" />
          </div>
        </div>

        {/* Chart Placeholder */}
        <Skeleton className="h-48 w-full" />

        {/* Rationale */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-16 w-full" />
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Skeleton className="h-10 flex-1" />
          <Skeleton className="h-10 w-24" />
        </div>
      </CardContent>
    </Card>
  );
}

export function TssProgressBarSkeleton() {
  return (
    <Card>
      <CardContent className="py-3">
        <div className="flex items-center justify-between mb-1.5">
          <Skeleton className="h-4 w-28" />
          <div className="flex items-center gap-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-10" />
          </div>
        </div>
        <Skeleton className="h-2.5 w-full rounded-full" />
      </CardContent>
    </Card>
  );
}

export function DashboardLoadingSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <FitnessCardSkeleton />
        <WellnessCardSkeleton />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <WeeklyCalendarSkeleton />
        <WeeklyPlanSkeleton />
      </div>

      <TodayWorkoutSkeleton />
    </div>
  );
}
