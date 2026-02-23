import {AuditForm, AuditPreview} from '@/components/pages/Home';

export default function Page() {
    return (
        <div className="mx-auto px-6 py-10">
            <div className="mb-8">
                <h1 className="text-3xl font-semibold tracking-tight">Automaton Auditor</h1>
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
