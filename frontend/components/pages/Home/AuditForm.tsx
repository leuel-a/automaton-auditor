'use client';

import {z} from 'zod';
import {zodResolver} from '@hookform/resolvers/zod';
import {useForm, Controller, type SubmitHandler} from 'react-hook-form';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {Card, CardTitle, CardHeader, CardContent} from '@/components/ui/card';
import {Field, FieldContent, FieldLabel, FieldError, FieldDescription} from '@/components/ui/field';

const auditSchema = z.object({
    githubUrl: z.url(),
    reportPdf: z.string(),
});

type AuditSchemaType = z.infer<typeof auditSchema>;

export function AuditForm() {
    const form = useForm<AuditSchemaType>({
        resolver: zodResolver(auditSchema),
        defaultValues: {
            githubUrl: '',
            reportPdf: '',
        },
    });

    const handleSubmit: SubmitHandler<AuditSchemaType> = (values) => {
        console.log(`Values: ${JSON.stringify(values)}`);
    };

    return (
        <Card className="h-fit rounded lg:col-span-3">
            <CardHeader>
                <CardTitle>Audit Inputs</CardTitle>
            </CardHeader>
            <CardContent>
                <form
                    className="space-y-6"
                    onSubmit={form.handleSubmit(handleSubmit)}
                >
                    <Controller
                        control={form.control}
                        name="githubUrl"
                        render={({field, fieldState}) => (
                            <Field>
                                <FieldLabel>GitHub Repository URL</FieldLabel>
                                <FieldContent>
                                    <Input
                                        {...field}
                                        placeholder="https://github.com/owner/repository"
                                    />
                                </FieldContent>
                                {fieldState.invalid ?? <FieldError errors={[fieldState.error]} />}
                            </Field>
                        )}
                    />
                    <Controller
                        control={form.control}
                        name="reportPdf"
                        render={({field, fieldState}) => (
                            <Field>
                                <FieldLabel>Rubric PDF Report</FieldLabel>
                                <FieldContent>
                                    <Input
                                        {...field}
                                        accept="application/pdf"
                                    />
                                    <FieldDescription className="text-muted-foreground text-xs">
                                        Upload the official evaluation rubric PDF.
                                    </FieldDescription>
                                </FieldContent>
                                {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                            </Field>
                        )}
                    />
                    <Button
                        className="my-4 w-full"
                        type="submit"
                    >
                        Run Audit
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
