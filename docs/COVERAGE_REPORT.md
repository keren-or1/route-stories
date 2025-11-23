============================= test session starts ==============================
platform darwin -- Python 3.11.8, pytest-9.0.1, pluggy-1.6.0 -- /opt/anaconda3/bin/python
cachedir: .pytest_cache
rootdir: /Users/keren/לימודים/רייכמן תואר שני/קורסים/סוכני llm/assignment4/route-stories
configfile: pytest.ini
plugins: anyio-4.11.0, asyncio-1.3.0, langsmith-0.4.42, cov-7.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 28 items

tests/agents/test_judge_agent.py::TestJudgeAgent::test_initialization PASSED [  3%]
tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_with_all_options FAILED [  7%]
tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_missing_content_option FAILED [ 10%]
tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_with_error_results FAILED [ 14%]
tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_claude_failure FAILED [ 17%]
tests/agents/test_song_agent.py::TestSongAgent::test_initialization PASSED [ 21%]
tests/agents/test_song_agent.py::TestSongAgent::test_execute_success FAILED [ 25%]
tests/agents/test_song_agent.py::TestSongAgent::test_execute_no_songs_found FAILED [ 28%]
tests/agents/test_song_agent.py::TestSongAgent::test_execute_with_claude_failure FAILED [ 32%]
tests/agents/test_story_agent.py::TestStoryAgent::test_initialization PASSED [ 35%]
tests/agents/test_story_agent.py::TestStoryAgent::test_execute_success FAILED [ 39%]
tests/agents/test_story_agent.py::TestStoryAgent::test_execute_no_stories_found FAILED [ 42%]
tests/agents/test_story_agent.py::TestStoryAgent::test_run_with_exception FAILED [ 46%]
tests/agents/test_video_agent.py::TestVideoAgent::test_initialization PASSED [ 50%]
tests/agents/test_video_agent.py::TestVideoAgent::test_execute_success PASSED [ 53%]
tests/agents/test_video_agent.py::TestVideoAgent::test_execute_no_videos_found PASSED [ 57%]
tests/agents/test_video_agent.py::TestVideoAgent::test_execute_claude_failure_fallback PASSED [ 60%]
tests/agents/test_video_agent.py::TestVideoAgent::test_parse_choice_valid PASSED [ 64%]
tests/agents/test_video_agent.py::TestVideoAgent::test_parse_choice_out_of_bounds PASSED [ 67%]
tests/agents/test_video_agent.py::TestVideoAgent::test_parse_choice_invalid_format PASSED [ 71%]
tests/agents/test_video_agent.py::TestVideoAgent::test_parse_reasoning_valid PASSED [ 75%]
tests/agents/test_video_agent.py::TestVideoAgent::test_parse_reasoning_missing PASSED [ 78%]
tests/agents/test_video_agent.py::TestVideoAgent::test_run_with_error_handling PASSED [ 82%]
tests/core/test_orchestrator.py::TestOrchestrator::test_initialization FAILED [ 85%]
tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_success FAILED [ 89%]
tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_with_agent_failure FAILED [ 92%]
tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_timeout_handling FAILED [ 96%]
tests/core/test_orchestrator.py::TestOrchestrator::test_parallel_execution FAILED [100%]

=================================== FAILURES ===================================
_________________ TestJudgeAgent.test_execute_with_all_options _________________

self = <test_judge_agent.TestJudgeAgent object at 0x1090fe650>
mock_claude_client = <Mock id='4446692304'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(story, point_id=1, status=SUCCESS)

    def test_execute_with_all_options(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test judge evaluation with all three content types."""
        # Mock three content options
        video_result = sample_agent_result
        video_result.agent_type = 'video'
        video_result.content = {'selected': {'title': 'Test Video'}}
    
        song_result = sample_agent_result
        song_result.agent_type = 'song'
        song_result.content = {'selected': {'title': 'Test Song'}}
    
        story_result = sample_agent_result
        story_result.agent_type = 'story'
        story_result.content = {'selected': {'title': 'Test Story'}}
    
        results = [video_result, song_result, story_result]
    
        mock_claude_client.structured_query.return_value = {
            'selected': 'video',
            'reasoning': 'Most visually engaging',
            'scores': {'video': 9.0, 'song': 7.5, 'story': 8.0},
            'confidence': 85
        }
    
        agent = JudgeAgent(mock_claude_client)
    
        # Create task with context containing results
        task = sample_agent_task
        task.context = {'agent_results': results}
    
        result = agent.execute(task)
    
        # Verify Claude was called
>       mock_claude_client.structured_query.assert_called_once()

tests/agents/test_judge_agent.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Mock name='mock.structured_query' id='4446684112'>

    def assert_called_once(self):
        """assert that the mock was called only once.
        """
        if not self.call_count == 1:
            msg = ("Expected '%s' to have been called once. Called %s times.%s"
                   % (self._mock_name or 'mock',
                      self.call_count,
                      self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'structured_query' to have been called once. Called 0 times.

/opt/anaconda3/lib/python3.11/unittest/mock.py:918: AssertionError
______________ TestJudgeAgent.test_execute_missing_content_option ______________

self = <test_judge_agent.TestJudgeAgent object at 0x1090fe410>
mock_claude_client = <Mock id='4447063120'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(song, point_id=1, status=SUCCESS)

    def test_execute_missing_content_option(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test judge handling when one content type is missing."""
        # Only provide video and song, no story
        video_result = sample_agent_result
        video_result.agent_type = 'video'
    
        song_result = sample_agent_result
        song_result.agent_type = 'song'
    
        results = [video_result, song_result]
    
        mock_claude_client.structured_query.return_value = {
            'selected': 'video',
            'reasoning': 'Best of available options',
            'scores': {'video': 8.0, 'song': 7.0},
            'confidence': 75
        }
    
        agent = JudgeAgent(mock_claude_client)
    
        task = sample_agent_task
        task.context = {'agent_results': results}
    
        result = agent.execute(task)
    
        # Should still work with partial results
>       assert result.error is None
E       AssertionError: assert 'No content results provided for judging' is None
E        +  where 'No content results provided for judging' = AgentResult(judge, point_id=1, status=ERROR).error

tests/agents/test_judge_agent.py:90: AssertionError
________________ TestJudgeAgent.test_execute_with_error_results ________________

self = <test_judge_agent.TestJudgeAgent object at 0x1090fdc50>
mock_claude_client = <Mock id='4447354960'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_error_result = AgentResult(story, point_id=1, status=ERROR)

    def test_execute_with_error_results(self, mock_claude_client, sample_agent_task, sample_error_result):
        """Test judge handling error results from content agents."""
        # All agents returned errors
        video_error = sample_error_result
        video_error.agent_type = 'video'
    
        song_error = sample_error_result
        song_error.agent_type = 'song'
    
        story_error = sample_error_result
        story_error.agent_type = 'story'
    
        results = [video_error, song_error, story_error]
    
        agent = JudgeAgent(mock_claude_client)
    
        task = sample_agent_task
        task.context = {'agent_results': results}
    
        result = agent.execute(task)
    
        # Should return error when no valid content available
        assert result.error is not None
>       assert "No valid content" in result.error or "all agents failed" in result.error.lower()
E       AssertionError: assert ('No valid content' in 'No content results provided for judging' or 'all agents failed' in 'no content results provided for judging')
E        +  where 'No content results provided for judging' = AgentResult(judge, point_id=1, status=ERROR).error
E        +  and   'no content results provided for judging' = <built-in method lower of str object at 0x10900c8d0>()
E        +    where <built-in method lower of str object at 0x10900c8d0> = 'No content results provided for judging'.lower
E        +      where 'No content results provided for judging' = AgentResult(judge, point_id=1, status=ERROR).error

tests/agents/test_judge_agent.py:116: AssertionError
__________________ TestJudgeAgent.test_execute_claude_failure __________________

self = <test_judge_agent.TestJudgeAgent object at 0x1090fe690>
mock_claude_client = <Mock id='4447261200'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(song, point_id=1, status=SUCCESS)

    def test_execute_claude_failure(self, mock_claude_client, sample_agent_task, sample_agent_result):
        """Test fallback when Claude API fails."""
        video_result = sample_agent_result
        video_result.agent_type = 'video'
    
        song_result = sample_agent_result
        song_result.agent_type = 'song'
    
        results = [video_result, song_result]
    
        # Simulate Claude failure
        mock_claude_client.structured_query.side_effect = Exception("API Error")
    
        agent = JudgeAgent(mock_claude_client)
    
        task = sample_agent_task
        task.context = {'agent_results': results}
    
        result = agent.execute(task)
    
        # Should return error result
        assert result.error is not None
>       assert "API Error" in result.error or "failed" in result.error.lower()
E       AssertionError: assert ('API Error' in 'No content results provided for judging' or 'failed' in 'no content results provided for judging')
E        +  where 'No content results provided for judging' = AgentResult(judge, point_id=1, status=ERROR).error
E        +  and   'no content results provided for judging' = <built-in method lower of str object at 0x10900c8d0>()
E        +    where <built-in method lower of str object at 0x10900c8d0> = 'No content results provided for judging'.lower
E        +      where 'No content results provided for judging' = AgentResult(judge, point_id=1, status=ERROR).error

tests/agents/test_judge_agent.py:140: AssertionError
______________________ TestSongAgent.test_execute_success ______________________

self = <test_song_agent.TestSongAgent object at 0x1090d2d90>
mock_claude_client = <Mock id='4447063696'>
mock_search_tools = <Mock id='4447061008'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
mock_song_results = [{'album': 'The Blueprint 3', 'artist': 'Jay-Z feat. Alicia Keys', 'duration': '4:36', 'title': 'Empire State of Mind'... New York', ...}, {'album': '1989', 'artist': 'Taylor Swift', 'duration': '3:32', 'title': 'Welcome to New York', ...}]

    def test_execute_success(self, mock_claude_client, mock_search_tools, sample_agent_task, mock_song_results):
        """Test successful song search and selection."""
        mock_search_tools.search_songs.return_value = mock_song_results
        mock_claude_client.simple_query.return_value = "CHOICE: 1\nREASONING: Perfect for NYC"
    
        agent = SongAgent(mock_claude_client, mock_search_tools)
>       result = agent.execute(sample_agent_task)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/agents/test_song_agent.py:28: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
agents/song_agent.py:53: in execute
    selected_song = self._select_best_song(task.address, songs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <agents.song_agent.SongAgent object at 0x10910fad0>
location = 'Times Square, New York, NY'
songs = <Mock name='mock.search_music()' id='4447066704'>

    def _select_best_song(
        self,
        location: str,
        songs: list
    ) -> Dict[str, Any]:
        """
        Use Claude to select the most relevant song.
    
        Args:
            location: Location name
            songs: List of song dictionaries
    
        Returns:
            Selected song with reasoning
        """
        # Build prompt for Claude
        songs_text = "\n\n".join([
            f"Song {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Artist: {s['artist']}\n"
            f"Genre: {s['genre']}\n"
            f"Duration: {s['duration']}\n"
            f"Album: {s['album']}"
>           for i, s in enumerate(songs)
                        ^^^^^^^^^^^^^^^^
        ])
E       TypeError: 'Mock' object is not iterable

agents/song_agent.py:89: TypeError
__________________ TestSongAgent.test_execute_no_songs_found ___________________

self = <test_song_agent.TestSongAgent object at 0x1090d0790>
mock_claude_client = <Mock id='4446708432'>
mock_search_tools = <Mock id='4446701136'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')

    def test_execute_no_songs_found(self, mock_claude_client, mock_search_tools, sample_agent_task):
        """Test behavior when no songs found."""
        mock_search_tools.search_songs.return_value = []
    
        agent = SongAgent(mock_claude_client, mock_search_tools)
>       result = agent.execute(sample_agent_task)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/agents/test_song_agent.py:45: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
agents/song_agent.py:53: in execute
    selected_song = self._select_best_song(task.address, songs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <agents.song_agent.SongAgent object at 0x1090b6090>
location = 'Times Square, New York, NY'
songs = <Mock name='mock.search_music()' id='4446706768'>

    def _select_best_song(
        self,
        location: str,
        songs: list
    ) -> Dict[str, Any]:
        """
        Use Claude to select the most relevant song.
    
        Args:
            location: Location name
            songs: List of song dictionaries
    
        Returns:
            Selected song with reasoning
        """
        # Build prompt for Claude
        songs_text = "\n\n".join([
            f"Song {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Artist: {s['artist']}\n"
            f"Genre: {s['genre']}\n"
            f"Duration: {s['duration']}\n"
            f"Album: {s['album']}"
>           for i, s in enumerate(songs)
                        ^^^^^^^^^^^^^^^^
        ])
E       TypeError: 'Mock' object is not iterable

agents/song_agent.py:89: TypeError
________________ TestSongAgent.test_execute_with_claude_failure ________________

self = <test_song_agent.TestSongAgent object at 0x1090d1290>
mock_claude_client = <Mock id='4446901712'>
mock_search_tools = <Mock id='4447370512'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
mock_song_results = [{'album': 'The Blueprint 3', 'artist': 'Jay-Z feat. Alicia Keys', 'duration': '4:36', 'title': 'Empire State of Mind'... New York', ...}, {'album': '1989', 'artist': 'Taylor Swift', 'duration': '3:32', 'title': 'Welcome to New York', ...}]

    def test_execute_with_claude_failure(self, mock_claude_client, mock_search_tools, sample_agent_task, mock_song_results):
        """Test fallback when Claude API fails."""
        mock_search_tools.search_songs.return_value = mock_song_results
        mock_claude_client.simple_query.side_effect = Exception("API timeout")
    
        agent = SongAgent(mock_claude_client, mock_search_tools)
>       result = agent.execute(sample_agent_task)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/agents/test_song_agent.py:56: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
agents/song_agent.py:53: in execute
    selected_song = self._select_best_song(task.address, songs)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <agents.song_agent.SongAgent object at 0x109154250>
location = 'Times Square, New York, NY'
songs = <Mock name='mock.search_music()' id='4447260816'>

    def _select_best_song(
        self,
        location: str,
        songs: list
    ) -> Dict[str, Any]:
        """
        Use Claude to select the most relevant song.
    
        Args:
            location: Location name
            songs: List of song dictionaries
    
        Returns:
            Selected song with reasoning
        """
        # Build prompt for Claude
        songs_text = "\n\n".join([
            f"Song {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Artist: {s['artist']}\n"
            f"Genre: {s['genre']}\n"
            f"Duration: {s['duration']}\n"
            f"Album: {s['album']}"
>           for i, s in enumerate(songs)
                        ^^^^^^^^^^^^^^^^
        ])
E       TypeError: 'Mock' object is not iterable

agents/song_agent.py:89: TypeError
_____________________ TestStoryAgent.test_execute_success ______________________

self = <test_story_agent.TestStoryAgent object at 0x1090a0550>
mock_claude_client = <Mock id='4447005136'>
mock_search_tools = <Mock id='4446999824'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
mock_story_results = [{'era': '1900s', 'source': 'NYC Historical Society', 'summary': 'In 1904, the area was renamed Times Square after The...uare earned its nickname in the 1920s when electric billboards illuminated Broadway.', 'title': 'The Great White Way'}]

    def test_execute_success(self, mock_claude_client, mock_search_tools, sample_agent_task, mock_story_results):
        """Test successful story search and selection."""
        mock_search_tools.search_stories.return_value = mock_story_results
        mock_claude_client.simple_query.return_value = "CHOICE: 1\nREASONING: Most interesting historical fact"
    
        agent = StoryAgent(mock_claude_client, mock_search_tools)
>       result = agent.execute(sample_agent_task)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/agents/test_story_agent.py:28: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
agents/story_agent.py:53: in execute
    selected_story = self._select_best_story(task.address, stories)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <agents.story_agent.StoryAgent object at 0x1090fea50>
location = 'Times Square, New York, NY'
stories = <Mock name='mock.search_historical_stories()' id='4446904144'>

    def _select_best_story(
        self,
        location: str,
        stories: list
    ) -> Dict[str, Any]:
        """
        Use Claude to select the most interesting story.
    
        Args:
            location: Location name
            stories: List of story dictionaries
    
        Returns:
            Selected story with reasoning
        """
        # Build prompt for Claude
        stories_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Content: {s['content']}\n"
            f"Source: {s['source']}\n"
            f"Period: {s['period']}\n"
            f"Category: {s['category']}"
>           for i, s in enumerate(stories)
                        ^^^^^^^^^^^^^^^^^^
        ])
E       TypeError: 'Mock' object is not iterable

agents/story_agent.py:89: TypeError
_________________ TestStoryAgent.test_execute_no_stories_found _________________

self = <test_story_agent.TestStoryAgent object at 0x1090a0cd0>
mock_claude_client = <Mock id='4446694672'>
mock_search_tools = <Mock id='4446692688'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')

    def test_execute_no_stories_found(self, mock_claude_client, mock_search_tools, sample_agent_task):
        """Test behavior when no stories found."""
        mock_search_tools.search_stories.return_value = []
    
        agent = StoryAgent(mock_claude_client, mock_search_tools)
>       result = agent.execute(sample_agent_task)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/agents/test_story_agent.py:45: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
agents/story_agent.py:53: in execute
    selected_story = self._select_best_story(task.address, stories)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <agents.story_agent.StoryAgent object at 0x1090b0cd0>
location = 'Times Square, New York, NY'
stories = <Mock name='mock.search_historical_stories()' id='4446689104'>

    def _select_best_story(
        self,
        location: str,
        stories: list
    ) -> Dict[str, Any]:
        """
        Use Claude to select the most interesting story.
    
        Args:
            location: Location name
            stories: List of story dictionaries
    
        Returns:
            Selected story with reasoning
        """
        # Build prompt for Claude
        stories_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"Title: {s['title']}\n"
            f"Content: {s['content']}\n"
            f"Source: {s['source']}\n"
            f"Period: {s['period']}\n"
            f"Category: {s['category']}"
>           for i, s in enumerate(stories)
                        ^^^^^^^^^^^^^^^^^^
        ])
E       TypeError: 'Mock' object is not iterable

agents/story_agent.py:89: TypeError
____________________ TestStoryAgent.test_run_with_exception ____________________

self = <test_story_agent.TestStoryAgent object at 0x1090a0c90>
mock_claude_client = <Mock id='4446629648'>
mock_search_tools = <Mock id='4446617936'>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')

    def test_run_with_exception(self, mock_claude_client, mock_search_tools, sample_agent_task):
        """Test error handling in run method."""
        mock_search_tools.search_stories.side_effect = ValueError("Invalid input")
    
        agent = StoryAgent(mock_claude_client, mock_search_tools)
        result = agent.run(sample_agent_task)
    
        # Should return error result, not crash
        assert result.error is not None
>       assert "Invalid input" in result.error
E       assert 'Invalid input' in "StoryAgent failed: 'Mock' object is not iterable"
E        +  where "StoryAgent failed: 'Mock' object is not iterable" = AgentResult(story, point_id=1, status=ERROR).error

tests/agents/test_story_agent.py:59: AssertionError
------------------------------ Captured log call -------------------------------
ERROR    route_stories.agent.StoryAgent:base_agent.py:99 StoryAgent failed: 'Mock' object is not iterable
_____________________ TestOrchestrator.test_initialization _____________________

self = <test_orchestrator.TestOrchestrator object at 0x1090e4910>

    def test_initialization(self):
        """Test orchestrator initialization."""
        mock_agents = {
            'video': Mock(),
            'song': Mock(),
            'story': Mock(),
            'judge': Mock()
        }
        mock_queue = Mock(spec=QueueManager)
    
        orchestrator = Orchestrator(
            video_agent=mock_agents['video'],
            song_agent=mock_agents['song'],
            story_agent=mock_agents['story'],
            judge_agent=mock_agents['judge'],
            queue_manager=mock_queue
        )
    
        assert orchestrator.video_agent == mock_agents['video']
        assert orchestrator.song_agent == mock_agents['song']
        assert orchestrator.story_agent == mock_agents['story']
        assert orchestrator.judge_agent == mock_agents['judge']
>       assert orchestrator.queue == mock_queue
               ^^^^^^^^^^^^^^^^^^
E       AttributeError: 'Orchestrator' object has no attribute 'queue'

tests/core/test_orchestrator.py:38: AttributeError
________________ TestOrchestrator.test_process_waypoint_success ________________

self = <test_orchestrator.TestOrchestrator object at 0x1090e4b90>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(judge, point_id=1, status=SUCCESS)

    def test_process_waypoint_success(self, sample_agent_task, sample_agent_result):
        """Test successful waypoint processing with all agents."""
        # Setup mock agents
        mock_video = Mock()
        mock_video.run.return_value = sample_agent_result
    
        mock_song = Mock()
        mock_song.run.return_value = sample_agent_result
    
        mock_story = Mock()
        mock_story.run.return_value = sample_agent_result
    
        mock_judge = Mock()
        judge_result = sample_agent_result
        judge_result.agent_type = 'judge'
        mock_judge.run.return_value = judge_result
    
        mock_queue = Mock(spec=QueueManager)
>       mock_queue.get_results_for_point.return_value = [
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            sample_agent_result,
            sample_agent_result,
            sample_agent_result
        ]

tests/core/test_orchestrator.py:58: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Mock spec='QueueManager' id='4447075600'>
name = 'get_results_for_point'

    def __getattr__(self, name):
        if name in {'_mock_methods', '_mock_unsafe'}:
            raise AttributeError(name)
        elif self._mock_methods is not None:
            if name not in self._mock_methods or name in _all_magics:
>               raise AttributeError("Mock object has no attribute %r" % name)
E               AttributeError: Mock object has no attribute 'get_results_for_point'

/opt/anaconda3/lib/python3.11/unittest/mock.py:653: AttributeError
__________ TestOrchestrator.test_process_waypoint_with_agent_failure ___________

self = <test_orchestrator.TestOrchestrator object at 0x1090e5f10>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(judge, point_id=1, status=SUCCESS)
sample_error_result = AgentResult(video, point_id=1, status=ERROR)

    def test_process_waypoint_with_agent_failure(self, sample_agent_task, sample_agent_result, sample_error_result):
        """Test waypoint processing when one agent fails."""
        # Video agent succeeds
        mock_video = Mock()
        mock_video.run.return_value = sample_agent_result
    
        # Song agent fails
        mock_song = Mock()
        mock_song.run.return_value = sample_error_result
    
        # Story agent succeeds
        mock_story = Mock()
        mock_story.run.return_value = sample_agent_result
    
        mock_judge = Mock()
        judge_result = sample_agent_result
        judge_result.agent_type = 'judge'
        mock_judge.run.return_value = judge_result
    
        mock_queue = Mock(spec=QueueManager)
>       mock_queue.get_results_for_point.return_value = [
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            sample_agent_result,
            sample_error_result,
            sample_agent_result
        ]

tests/core/test_orchestrator.py:108: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Mock spec='QueueManager' id='4446815824'>
name = 'get_results_for_point'

    def __getattr__(self, name):
        if name in {'_mock_methods', '_mock_unsafe'}:
            raise AttributeError(name)
        elif self._mock_methods is not None:
            if name not in self._mock_methods or name in _all_magics:
>               raise AttributeError("Mock object has no attribute %r" % name)
E               AttributeError: Mock object has no attribute 'get_results_for_point'

/opt/anaconda3/lib/python3.11/unittest/mock.py:653: AttributeError
___________ TestOrchestrator.test_process_waypoint_timeout_handling ____________

self = <test_orchestrator.TestOrchestrator object at 0x1090e5c10>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')

    def test_process_waypoint_timeout_handling(self, sample_agent_task):
        """Test timeout handling for slow agents."""
        # Create agents that simulate slow execution
        import time
    
        def slow_agent_run(task):
            time.sleep(0.1)  # Simulate work
            return sample_agent_result
    
        mock_video = Mock()
        mock_video.run = slow_agent_run
    
        mock_song = Mock()
        mock_song.run = slow_agent_run
    
        mock_story = Mock()
        mock_story.run = slow_agent_run
    
        mock_judge = Mock()
>       mock_judge.run.return_value = sample_agent_result
                                      ^^^^^^^^^^^^^^^^^^^
E       NameError: name 'sample_agent_result' is not defined

tests/core/test_orchestrator.py:147: NameError
___________________ TestOrchestrator.test_parallel_execution ___________________

self = <test_orchestrator.TestOrchestrator object at 0x1090e6390>
sample_agent_task = AgentTask(route=test-route-001, point=1, address='Times Square, New York, NY')
sample_agent_result = AgentResult(video, point_id=1, status=SUCCESS)

    def test_parallel_execution(self, sample_agent_task, sample_agent_result):
        """Test that content agents run in parallel."""
        import threading
        execution_times = []
    
        def timed_run(task):
            import time
            start = time.time()
            time.sleep(0.05)  # Simulate work
            execution_times.append((threading.current_thread().name, time.time() - start))
            return sample_agent_result
    
        mock_video = Mock()
        mock_video.run = timed_run
    
        mock_song = Mock()
        mock_song.run = timed_run
    
        mock_story = Mock()
        mock_story.run = timed_run
    
        mock_judge = Mock()
        mock_judge.run.return_value = sample_agent_result
    
        mock_queue = Mock(spec=QueueManager)
>       mock_queue.get_results_for_point.return_value = [
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            sample_agent_result,
            sample_agent_result,
            sample_agent_result
        ]

tests/core/test_orchestrator.py:189: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Mock spec='QueueManager' id='4447119248'>
name = 'get_results_for_point'

    def __getattr__(self, name):
        if name in {'_mock_methods', '_mock_unsafe'}:
            raise AttributeError(name)
        elif self._mock_methods is not None:
            if name not in self._mock_methods or name in _all_magics:
>               raise AttributeError("Mock object has no attribute %r" % name)
E               AttributeError: Mock object has no attribute 'get_results_for_point'

/opt/anaconda3/lib/python3.11/unittest/mock.py:653: AttributeError
================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.11.8-final-0 _______________

Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
agents/__init__.py                     6      0   100%
agents/base_agent.py                  41      4    90%   59, 122-127
agents/judge_agent.py                 95     80    16%   44-98, 116-187, 196-203, 207-214, 218-230
agents/song_agent.py                  49     30    39%   46, 56-64, 92-129, 133-140, 144-147
agents/story_agent.py                 49     30    39%   46, 56-64, 92-130, 134-141, 145-148
agents/video_agent.py                 49      0   100%
config.py                             28     28     0%   6-75
core/__init__.py                       4      0   100%
core/collector.py                    121     91    25%   32-33, 50-53, 74-105, 117, 126-127, 136-138, 147-168, 182-189, 193-244
core/orchestrator.py                  50     30    40%   70-133, 146, 150-152
core/scheduler.py                     47     34    28%   26-29, 38, 47-52, 61-68, 77, 87-89, 103-125, 134
demo_execution.py                    145    145     0%   8-313
main.py                               93     93     0%   7-201
services/__init__.py                   4      0   100%
services/claude_client.py             67     55    18%   36-40, 64-85, 104-105, 124-132, 151-177, 185-191, 204-232
services/google_maps.py              101     71    30%   25, 39, 56-57, 81-123, 140-200, 213-224, 236-243, 256-262
services/search_tools.py              36     24    33%   23-27, 44-79, 96-131, 148-183, 195-201, 214-220
test_setup.py                        108    108     0%   7-205
tests/agents/test_judge_agent.py      72      7    90%   57-62, 91
tests/agents/test_song_agent.py       35     11    69%   31-38, 47-48, 59-61
tests/agents/test_story_agent.py      33      8    76%   31-38, 47-48
tests/agents/test_video_agent.py      70      0   100%
tests/conftest.py                     39      0   100%
tests/core/test_orchestrator.py       96     29    70%   64-86, 114-126, 134-135, 149-162, 170-174, 195-211
ui/__init__.py                         2      2     0%   3-5
ui/cli.py                            132    132     0%   5-276
utils/__init__.py                      3      0   100%
utils/logger.py                       37     25    32%   26-28, 51-83
utils/queue_manager.py                66     38    42%   40-43, 52-64, 76-79, 96-97, 114-116, 128-129, 138-141, 145, 168-183
----------------------------------------------------------------
TOTAL                               1678   1075    36%
Coverage HTML written to dir htmlcov
=========================== short test summary info ============================
FAILED tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_with_all_options
FAILED tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_missing_content_option
FAILED tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_with_error_results
FAILED tests/agents/test_judge_agent.py::TestJudgeAgent::test_execute_claude_failure
FAILED tests/agents/test_song_agent.py::TestSongAgent::test_execute_success
FAILED tests/agents/test_song_agent.py::TestSongAgent::test_execute_no_songs_found
FAILED tests/agents/test_song_agent.py::TestSongAgent::test_execute_with_claude_failure
FAILED tests/agents/test_story_agent.py::TestStoryAgent::test_execute_success
FAILED tests/agents/test_story_agent.py::TestStoryAgent::test_execute_no_stories_found
FAILED tests/agents/test_story_agent.py::TestStoryAgent::test_run_with_exception
FAILED tests/core/test_orchestrator.py::TestOrchestrator::test_initialization
FAILED tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_success
FAILED tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_with_agent_failure
FAILED tests/core/test_orchestrator.py::TestOrchestrator::test_process_waypoint_timeout_handling
FAILED tests/core/test_orchestrator.py::TestOrchestrator::test_parallel_execution
======================== 15 failed, 13 passed in 1.22s =========================
