export const WIDGET_SCHEMA_LITERAL = {
    version: 4,
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
            type: 'string' // The React code for the widget
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
        createdAt: {
            type: 'number'
        }
    },
    required: ['id', 'title', 'code']
} as const;
