'use server';

import httpStatus from 'http-status';
import {API_ROUTES} from '@/config/routes';

type ActionState<T = any> = {
    success: boolean;
    status: number;
    data?: T;
    error?: string;
};

type HealthCheckResponse = {
    running: boolean;
};

export async function getServerState(): Promise<ActionState<HealthCheckResponse>> {
    try {
        const response = await fetch(API_ROUTES.healthcheck, {
            method: 'GET',
            cache: 'no-store',
        });

        if (!response.ok) {
            return {
                success: false,
                status: response.status,
                error: `Request failed with status: ${response.status}`,
            };
        }

        const responseData = await response.json();
        return {
            success: true,
            status: response.status,
            data: responseData,
        };
    } catch (error) {
        return {
            success: false,
            status: httpStatus.INTERNAL_SERVER_ERROR,
            error: error instanceof Error ? error.message : 'unknown error',
        };
    }
}
