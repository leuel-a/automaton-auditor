import {Badge} from '@/components/ui/badge';
import {AuditForm, AuditPreview} from '@/components/pages/Home';
import {getServerState} from './actions';
import {cn} from '@/lib/utils';

export default async function Page() {
    const {data, success} = await getServerState();

    return (
        <div className="mx-auto px-6 py-10">
            <div className="mb-8">
                <div className="flex justify-between">
                    <h1 className="text-3xl font-semibold tracking-tight">Automaton Auditor</h1>
                    <Badge
                        className={cn(
                            'h-10 w-12 text-lg',
                            success && data?.running ? 'bg-green-500' : 'bg-yellow-400',
                        )}
                    >
                        {success && data?.running ? 'up' : 'down'}
                    </Badge>
                </div>
                <p className="text-muted-foreground mt-2 text-sm">
                    Provide a GitHub repository URL and the PDF Report to generate an audit report.
                </p>
            </div>
            <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
                <AuditForm />
                <AuditPreview />
            </div>
        </div>
    );
}
