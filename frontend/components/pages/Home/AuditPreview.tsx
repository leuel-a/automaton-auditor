import {Download} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Card, CardContent, CardHeader, CardTitle} from '@/components/ui/card';
import {Textarea} from '@/components/ui/textarea';

const TEXT_AREA_DEFAULT_TEXT = `
# Audit Report

Repository: github.com/example/repo

## Git History
- 12 commits detected
- Progressive atomic development observed

## Tool Wiring
✓ Required tools exported
✓ Middleware properly registered

## Sidecar Artifacts
✓ .orchestration/active_intents.yaml
✓ agent_trace.jsonl

## Verdict
This repository demonstrates structured orchestration and functional integration.

Score: 4 / 5
`;

export function AuditPreview() {
    return (
        <Card className="flex h-150 flex-col lg:col-span-9 rounded">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Audit Preview</CardTitle>
                <Button
                    variant="outline"
                    size="sm"
                >
                    <Download className="mr-2 h-4 w-4" />
                    Download
                </Button>
            </CardHeader>

            <CardContent className="flex-1 overflow-y-auto">
                <div className="bg-muted/30 h-full rounded-md border p-4">
                    <Textarea
                        readOnly
                        className="h-full resize-none border-0 bg-transparent p-0 focus-visible:ring-0"
                        defaultValue={TEXT_AREA_DEFAULT_TEXT}
                    />
                </div>
            </CardContent>
        </Card>
    );
}
