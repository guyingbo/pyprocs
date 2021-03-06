import asyncio
import multiprocessing
import signal
import sys
import time
from typing import List, Union

import async_timeout
import typer

__version__ = "0.1.1"


class Supervisor:
    def __init__(
        self,
        exec_args: List[str],
        sys_exec: bool,
        stop_timeout: Union[int, float],
        num_workers: int,
        failed_seconds: Union[int, float],
        restart_wait: Union[int, float],
    ):
        self.exec_args = exec_args
        self.stop_timeout = stop_timeout
        self.num_workers = num_workers
        self.failed_seconds = failed_seconds
        self.restart_wait = restart_wait
        self.processes = set()
        self.tasks = set()
        if sys_exec:
            self.exec_args.insert(0, sys.executable)
        self._quit = False

    async def run_forever(self):
        self._event = asyncio.Event()
        self.register_signals()
        await self._create_processes()
        while not self._quit:
            await self._event.wait()
            if self._quit:
                break
            await self._create_processes()
            self._event.clear()
        # quit
        for p in self.processes:
            if p.returncode is None:
                p.terminate()
        try:
            for task in asyncio.as_completed(self.tasks, timeout=self.stop_timeout):
                await task
        except asyncio.TimeoutError:
            for p in self.processes:
                if p.returncode is None:
                    p.kill()
            await asyncio.wait(self.tasks)

    async def _create_processes(self):
        # cleanup
        to_remove = []
        for p in self.processes:
            if p.returncode is not None:
                to_remove.append(p)
        for p in to_remove:
            self.processes.remove(p)
        for _ in range(self.num_workers - len(self.processes)):
            await self._create_one_process()

    async def _create_one_process(self):
        p = await asyncio.create_subprocess_exec(
            *self.exec_args, start_new_session=True
        )
        self.processes.add(p)
        # task = asyncio.create_task(self.monitor_process(p))
        # for python 3.6
        task = asyncio.ensure_future(self.monitor_process(p))
        self.tasks.add(task)
        task.add_done_callback(self.task_done)

    async def monitor_process(self, p):
        start = time.time()
        returncode = await p.wait()
        end = time.time()
        elapse = end - start
        if returncode != 0 or (
            elapse < self.failed_seconds and not self._event.is_set()
        ):
            print(
                f"Process {p.pid} exit with code {returncode} in {elapse:.1f} seconds.",
                file=sys.stderr,
            )
            try:
                async with async_timeout.timeout(self.restart_wait):
                    await self._event.wait()
            except asyncio.TimeoutError:
                pass

    def task_done(self, task):
        self.tasks.remove(task)
        self._event.set()

    def register_signals(self):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self.handle_quit)
        loop.add_signal_handler(signal.SIGTERM, self.handle_quit)

    def handle_quit(self):
        self._quit = True
        self._event.set()


def main(
    exec_args: List[str] = typer.Argument(..., metavar="command", clamp=True),
    num_workers: int = typer.Option(
        multiprocessing.cpu_count(),
        "-w",
        "--num-workers",
        help="number of worker processes, default to cpu count",
    ),
    stop_timeout: int = typer.Option(
        10,
        "--graceful-timeout",
        metavar="SECONDS",
        help="seconds to wait before force killing processes",
    ),
    sys_exec: bool = typer.Option(
        False,
        "-s",
        "--sys-executable",
        help=f"use current python executable ({sys.executable}) to run command",
    ),
    restart_wait: float = typer.Option(
        5,
        "-t",
        "--restart-wait",
        metavar="SECONDS",
        help="seconds to wait before restart failed process (exit code != 0)",
    ),
    failed_seconds: float = typer.Option(
        3,
        "--failure-threshold",
        metavar="SECONDS",
        help="process exit within N seconds is also considered as a failure",
    ),
):
    "Multiprocess manager"
    supervisor = Supervisor(
        exec_args, sys_exec, stop_timeout, num_workers, failed_seconds, restart_wait
    )

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(supervisor.run_forever())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        asyncio.set_event_loop(None)
        loop.close()


if __name__ == "__main__":
    typer.run(main)
