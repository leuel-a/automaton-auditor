'use client';

import {z} from 'zod';
import {zodResolver} from '@hookform/resolvers/zod';
import {useForm, Controller, type SubmitHandler} from 'react-hook-form';
import {Input} from '@/components/ui/input';
import {Button} from '@/components/ui/button';
import {Card, CardTitle, CardHeader, CardContent} from '@/components/ui/card';
import {Field, FieldContent, FieldLabel, FieldError, FieldDescription} from '@/components/ui/field';

const auditSchema = z.object({
    githubUrl: z.url({ message: 'Github URL must be a valid URL' }),
    reportPdf: z
        .instanceof(File, { message: 'Please choose a file' })
        .refine((file) => file.size <= 5 * 1024 * 1024, {
            message: 'File must be less than 5MB',
        })
        .refine((file) => file.type === 'application/pdf', {
            message: 'Only PDF files are allowed',
        }),
});

type AuditSchemaType = z.infer<typeof auditSchema>;

export function AuditForm() {
    const form = useForm<AuditSchemaType>({
        resolver: zodResolver(auditSchema),
        defaultValues: {
            githubUrl: '',
            reportPdf: undefined,
        },
    });

    const handleSubmit: SubmitHandler<AuditSchemaType> = (values) => {
        console.log(`Values: ${JSON.stringify(values)}`);
    };

    return (
        <Card className="h-fit rounded lg:col-span-3">
            <CardHeader>
                <CardTitle>Audit</CardTitle>
            </CardHeader>
            <CardContent>
                <form
                    noValidate
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
                                        type="url"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="https://github.com/owner/repository"
                                    />
                                </FieldContent>
                                {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
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
                                        accept="application/pdf"
                                        aria-invalid={fieldState.invalid}
                                        className="cursor-pointer"
                                        onChange={(event) => field.onChange(event.target.files?.[0])}
                                        type="file"
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
                        className="my-4 w-full cursor-pointer"
                        type="submit"
                    >
                        Run Audit
                    </Button>
                </form>
            </CardContent>
        </Card>
    );
}
