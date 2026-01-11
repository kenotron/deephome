export const WIDGET_SCHEMA_LITERAL = {
    version: 7,
    primaryKey: 'id',
    type: 'object',
    properties: {
        id: {
            type: 'string',
            maxLength: 100
        },
        title: {
            type: 'string'
        },
        code: {
            type: ['string', 'null'] // The React code for the widget (nullable if using url)
        },
        url: {
            type: ['string', 'null'] // URL can be null for code-only widgets
        },
        dimensions: {
            type: 'object',
            properties: {
                w: { type: 'number' },
                h: { type: 'number' }
            }
        },
        x: { type: 'number' },
        y: { type: 'number' },
        sessionId: {
            type: ['string', 'null'] // Agent session ID for editing continuity
        },
        projectPath: {
            type: ['string', 'null'] // Filesystem path to widget's project directory
        },
        createdAt: {
            type: 'number'
        }
    },
    required: ['id', 'title']
} as const;
