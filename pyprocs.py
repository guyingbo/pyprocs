import sys
import time
import signal
import asyncio
import argparse
import async_timeout
import multiprocessing

__version__ = "0.1.1"


class Supervisor:
    def __init__(self, args):
        self.args = args
        self.processes = set()
        self.tasks = set()
        self.exec_args = self.args.process_args[:]
        if self.args.sys_exec:
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
            for task in asyncio.as_completed(
                self.tasks, timeout=self.args.stop_timeout
            ):
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
        for _ in range(self.args.num_workers - len(self.processes)):
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
        if returncode != 0 or (elapse < self.args.bad_seconds):
            print(
                f"Process {p.pid} exit with code {returncode} in {elapse:.1f} seconds.",
                file=sys.stderr,
            )
            try:
                async with async_timeout.timeout(self.args.restart_wait):
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


def main(arguments=None):
    parser = argparse.ArgumentParser(description="Multiprocess manager")
    parser.add_argument("process_args", metavar="ARG", nargs="+", help="program to run")
    parser.add_argument(
        "-w",
        "--num_workers",
        type=int,
        default=multiprocessing.cpu_count(),
        help=f"number of worker processes, default to cpu count",
    )
    parser.add_argument(
        "--graceful-timeout",
        metavar="SECONDS",
        dest="stop_timeout",
        type=int,
        default=10,
        help="seconds to wait before force killing processes",
    )
    parser.add_argument(
        "-s",
        "--sys-executable",
        dest="sys_exec",
        action="store_true",
        default=False,
        help=f"use system python executable ({sys.executable}) to run command",
    )
    parser.add_argument(
        "-t",
        "--restart-wait",
        metavar="SECONDS",
        dest="restart_wait",
        type=int,
        default=5,
        help="seconds to wait before restart bad process (exit code != 0)",
    )
    parser.add_argument(
        "--bad-threshold",
        metavar="SECONDS",
        dest="bad_seconds",
        type=int,
        default=3,
        help="process exit within n seconds is also considered as bad process",
    )
    args = parser.parse_args(arguments)
    supervisor = Supervisor(args)
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(supervisor.run_forever())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        asyncio.set_event_loop(None)
        loop.close()


if __name__ == "__main__":
    main()
