"""
Chat Application Server Module

This package contains all server-side implementations for the chat application.

Main Components:
- server.py: Main server startup script with command-line parameter support
- server_network.py: Core network communication and message handling
- server_ui.py: Traditional server UI interface using Qt Designer
- modern_server_ui.py: Modern server UI using rrd_widgets components

Features:
- Multi-client connection management
- UDP broadcast and server discovery
- TCP message routing and forwarding
- Group creation and management
- Reminder service implementation
- Translation service support
- Cross-server communication
- Client heartbeat monitoring
- Message logging and history
- Real-time status monitoring

The server acts as a central hub for all client communications,
managing user sessions, group memberships, and message delivery
across the network infrastructure.
""" 