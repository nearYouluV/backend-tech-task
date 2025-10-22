-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_occurred_at ON events(occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_user_occurred ON events(user_id, occurred_at);

-- Grant permissions to events_user
GRANT ALL ON SCHEMA public TO events_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO events_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO events_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO events_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO events_user;
