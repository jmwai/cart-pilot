"""
Session manager for handling ADK session creation, retrieval, and state management.

This module provides a centralized interface for managing sessions and their state,
with special handling for image persistence.
"""

import logging
from typing import Dict, Optional, Any

from google.adk.runners import Runner

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages ADK sessions and their state."""

    def __init__(self, runner: Runner, agent_name: str, debug: bool = False):
        """Initialize session manager.
        
        Args:
            runner: ADK Runner instance
            agent_name: Name of the agent
            debug: Enable debug logging (default: False)
        """
        self.runner = runner
        self.agent_name = agent_name
        self.debug = debug

    async def get_or_create_session(
        self,
        user_id: str,
        session_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get existing session or create new one.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            initial_state: Optional initial state dictionary
            
        Returns:
            Session object
            
        Raises:
            ValueError: If session creation fails
        """
        # Always try to get existing session first to preserve state
        session = None
        try:
            session = await self.runner.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id
            )
            if self.debug and session and hasattr(session, 'state'):
                state_keys = list(session.state.keys()) if session.state else []
                logger.info(
                    f"DEBUG: Retrieved existing session {session_id} with state keys: {state_keys}")
        except Exception as e:
            # Session doesn't exist or error occurred
            if self.debug:
                logger.info(
                    f"DEBUG: Session {session_id} get_session raised exception: {e}")

        # If session is None, create new one
        if session is None:
            if self.debug:
                logger.info(
                    f"DEBUG: Session {session_id} not found, creating new one (app_name={self.agent_name}, user_id={user_id})")
            
            initial_state = initial_state or {}
            try:
                session = await self.runner.session_service.create_session(
                    app_name=self.agent_name,
                    user_id=user_id,
                    state=initial_state,
                    session_id=session_id,
                )
                if self.debug:
                    logger.info(
                        f"DEBUG: Successfully created session {session_id} with initial state keys: {list(initial_state.keys())}")
            except Exception as create_error:
                logger.error(
                    f"DEBUG: Failed to create session {session_id}: {create_error}")
                raise ValueError(
                    f"Failed to create session with id: {session_id} (app_name={self.agent_name}, user_id={user_id}): {create_error}")

        # Verify session was created/retrieved
        if not session:
            raise ValueError(
                f"Failed to create or retrieve session with id: {session_id} (app_name={self.agent_name}, user_id={user_id})")

        return session

    async def update_session_state(
        self,
        session: Any,
        user_id: str,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Any:
        """Update session state and verify persistence.
        
        Args:
            session: Session object
            user_id: User identifier
            session_id: Session identifier
            updates: Dictionary of state updates
            
        Returns:
            Updated session object
        """
        # Ensure session has state dictionary
        if not hasattr(session, 'state') or session.state is None:
            session.state = {}

        # Apply updates
        session.state.update(updates)

        if self.debug:
            logger.info(
                f"DEBUG: Updated session {session_id} state with keys: {list(updates.keys())}")
            logger.info(
                f"DEBUG: Session state keys after update: {list(session.state.keys())}")

        # Explicitly update session to ensure persistence
        try:
            if hasattr(self.runner.session_service, 'update_session'):
                await self.runner.session_service.update_session(session)
                if self.debug:
                    logger.info(f"DEBUG: Called update_session to persist state")
        except Exception as update_error:
            logger.warning(
                f"DEBUG: update_session not available or failed: {update_error}")

        # Verify persistence by re-fetching
        try:
            verify_session = await self.runner.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id
            )
            if verify_session and hasattr(verify_session, 'state'):
                verify_keys = list(
                    verify_session.state.keys()) if verify_session.state else []
                verify_updates = all(
                    verify_session.state.get(key) == value
                    for key, value in updates.items()
                )
                if self.debug:
                    logger.info(
                        f"DEBUG: Verified session state - keys: {verify_keys}, updates present: {verify_updates}")

                # If verification failed, re-apply updates
                if not verify_updates:
                    if self.debug:
                        logger.warning(
                            f"DEBUG: State not persisted correctly, re-applying updates")
                    verify_session.state.update(updates)
                    if hasattr(self.runner.session_service, 'update_session'):
                        await self.runner.session_service.update_session(verify_session)
                    return verify_session
        except Exception as verify_error:
            if self.debug:
                logger.error(
                    f"DEBUG: Could not verify session state: {verify_error}")

        return session

    async def get_session_state(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get current session state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dictionary containing session state
        """
        try:
            session = await self.runner.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id
            )
            if session and hasattr(session, 'state'):
                return session.state if session.state else {}
        except Exception as e:
            if self.debug:
                logger.info(
                    f"DEBUG: Could not get session state: {e}")
        return {}

    async def get_session(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[Any]:
        """Get session object.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Session object or None if not found
        """
        try:
            return await self.runner.session_service.get_session(
                app_name=self.agent_name,
                user_id=user_id,
                session_id=session_id
            )
        except Exception:
            return None

