import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import type { WorkoutGenerateRequest } from "@/lib/api";

interface WorkoutFormProps {
    onGenerate: (request: WorkoutGenerateRequest) => void;
    isLoading: boolean;
}

const STYLES = [
    { value: "auto", label: "자동 (TSB 기반)" },
    { value: "polarized", label: "양극화 (80/20)" },
    { value: "norwegian", label: "노르웨이식 (역치)" },
    { value: "sweetspot", label: "스윗스팟" },
    { value: "threshold", label: "역치 중심" },
    { value: "endurance", label: "지구력" },
];

const INTENSITIES = [
    { value: "auto", label: "자동" },
    { value: "easy", label: "쉽게 😌" },
    { value: "moderate", label: "적당히 💪" },
    { value: "hard", label: "빡세게 🔥" },
];

export function WorkoutForm({ onGenerate, isLoading }: WorkoutFormProps) {
    const [duration, setDuration] = useState(60);
    const [style, setStyle] = useState("auto");
    const [intensity, setIntensity] = useState("auto");
    const [notes, setNotes] = useState("");
    const [indoor, setIndoor] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onGenerate({
            duration,
            style,
            intensity,
            notes,
            indoor,
        });
    };

    return (
        <Card className="w-full">
            <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                    🚴 워크아웃 생성
                </CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Duration Slider */}
                    <div className="space-y-2">
                        <Label>목표 시간: {duration}분</Label>
                        <Slider
                            value={[duration]}
                            onValueChange={(v) => setDuration(v[0])}
                            min={30}
                            max={120}
                            step={15}
                            className="w-full"
                        />
                        <div className="flex justify-between text-xs text-muted-foreground">
                            <span>30분</span>
                            <span>120분</span>
                        </div>
                    </div>

                    {/* Style Select */}
                    <div className="space-y-2">
                        <Label>훈련 스타일</Label>
                        <Select value={style} onValueChange={setStyle}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {STYLES.map((s) => (
                                    <SelectItem key={s.value} value={s.value}>
                                        {s.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Intensity Select */}
                    <div className="space-y-2">
                        <Label>강도 선호</Label>
                        <Select value={intensity} onValueChange={setIntensity}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                {INTENSITIES.map((i) => (
                                    <SelectItem key={i.value} value={i.value}>
                                        {i.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Notes Input */}
                    <div className="space-y-2">
                        <Label>추가 요청 (선택)</Label>
                        <Input
                            placeholder="예: 오늘 다리가 무거워요..."
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                        />
                    </div>

                    {/* Indoor Toggle */}
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            id="indoor"
                            checked={indoor}
                            onChange={(e) => setIndoor(e.target.checked)}
                            className="rounded"
                        />
                        <Label htmlFor="indoor">🏠 실내 트레이너</Label>
                    </div>

                    {/* Submit Button */}
                    <Button type="submit" className="w-full" disabled={isLoading}>
                        {isLoading ? "생성 중..." : "🎯 워크아웃 생성"}
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
